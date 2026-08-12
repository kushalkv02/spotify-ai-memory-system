"""LangGraph workflow that automates a complete chatbot recommendation turn.

The graph coordinates existing services; it never replaces the durable event
or graph stores.  Its nodes make each stage observable and independently
extendable (for example, adding moderation or human review before ``persist``).
"""
from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from ..models.event import EventEnvelope, RawEventRecord
from ..models.event_types import EventCategory
from ..orchestrator import InteractionOrchestrator
from ..integrations.graph_client import GraphClient
from .chat_assistant import ChatTurn, PreferenceSignal, chat_assistant
from .client_state_service import client_state


class ChatWorkflowState(TypedDict, total=False):
    user_id: str
    content: str
    context: list[dict[str, str]]
    legacy_preference: dict[str, Any] | None
    turn: ChatTurn
    signals: list[PreferenceSignal]
    event: RawEventRecord
    graph_recommendations: list[dict[str, Any]]
    memory_context: list[dict[str, Any]]
    preference_context: list[dict[str, Any]]
    reasoning_context: list[dict[str, Any]]
    explanation_context: str
    graph_evidence_used: bool
    gemini_recommendation_used: bool
    recommended: list[dict[str, Any]]
    recommendation_reason: str
    reply_content: str


class ChatRecommendationWorkflow:
    """One deterministic LangGraph run for one incoming chat message."""

    def __init__(self, orchestrator: InteractionOrchestrator, graph_client: GraphClient) -> None:
        self.orchestrator = orchestrator
        self.graph_client = graph_client
        builder = StateGraph(ChatWorkflowState)
        builder.add_node("understand", self.understand)
        builder.add_node("persist", self.persist)
        builder.add_node("project_preferences", self.project_preferences)
        builder.add_node("recommend", self.recommend)
        builder.add_node("compose_reply", self.compose_reply)
        builder.add_edge(START, "understand")
        builder.add_edge("understand", "persist")
        builder.add_edge("persist", "project_preferences")
        builder.add_edge("project_preferences", "recommend")
        builder.add_edge("recommend", "compose_reply")
        builder.add_edge("compose_reply", END)
        self.graph = builder.compile()

    async def run(
        self, *, user_id: str, content: str, context: list[dict[str, str]], legacy_preference: dict[str, Any] | None = None
    ) -> ChatWorkflowState:
        return await self.graph.ainvoke({
            "user_id": user_id, "content": content, "context": context[-10:],
            "legacy_preference": legacy_preference,
        })

    async def understand(self, state: ChatWorkflowState) -> dict[str, Any]:
        turn = await chat_assistant.respond(
            content=state["content"], context=state["context"], catalog=client_state.tracks,
        )
        signals = list(turn.preferences)
        if state.get("legacy_preference"):
            signals.append(PreferenceSignal(**state["legacy_preference"]))
        # Last declaration wins when an old UI client submits an explicit
        # structured preference that differs from the natural-language parse.
        unique = {(signal.kind, signal.value.casefold()): signal for signal in signals}
        return {"turn": turn, "signals": list(unique.values())}

    async def persist(self, state: ChatWorkflowState) -> dict[str, Any]:
        print(f"Persisting {len(state['signals'])} preference signals for user {state['user_id']}")
        event = await self.orchestrator.ingest(
            EventEnvelope(
                user_id=state["user_id"], category=EventCategory.CHAT,
                payload={
                    "message": state["content"], "user_display_name": "Listener",
                    "context": state["context"], "explicit_preference": bool(state["signals"]),
                    "extracted_preferences": [signal.model_dump() for signal in state["signals"]],
                },
            ),
            require_graph_writeback=True,
        )
        return {"event": event}

    async def project_preferences(self, state: ChatWorkflowState) -> dict[str, Any]:
        print(f"Projecting {len(state['signals'])} preference signals for user {state['user_id']} (event: {state['event'].event_id})")
        memory_strength = float(state["event"].importance_score or 0.0)
        weighted_signals = [
            signal.model_copy(update={"strength": round(signal.strength * memory_strength, 3)})
            for signal in state["signals"]
        ]
        for preference in weighted_signals:
            await self.graph_client.set_explicit_preference(
                user_id=state["user_id"], kind=preference.kind, value=preference.value,
                sentiment=preference.sentiment, strength=preference.strength,
            )
        client_state.apply_chat_preferences(
            state["user_id"], [signal.model_dump() for signal in weighted_signals]
        )
        evidence = await self.graph_client.recommendation_evidence_for_user(
            state["user_id"], state["content"], recommendation_limit=12,
            memory_limit=6, preference_limit=12, reasoning_days=30, reasoning_limit=12,
        )
        memory_context = evidence["memory_context"]
        # The current event has already been written to Neo4j. Include its
        # accepted memory immediately while retrieval indexes catch up.
        if state["event"].is_important:
            memory_context.insert(0, {"summary": state["content"], "strength": memory_strength, "memory_class": "current_turn"})
        return {
            "graph_recommendations": evidence["graph_recommendations"],
            "memory_context": memory_context,
            "preference_context": evidence["preference_context"],
            "reasoning_context": evidence["reasoning_context"],
            "explanation_context": evidence.get("explanation_context", ""),
            "graph_evidence_used": True,
        }

    async def recommend(self, state: ChatWorkflowState) -> dict[str, Any]:
        graph_track_ids = [item["track_id"] for item in state["graph_recommendations"] if item.get("track_id")]
        candidates = client_state.recommend(state["user_id"], limit=12, graph_track_ids=graph_track_ids)
        plan = await chat_assistant.recommend_tracks(
            candidates=candidates,
            memories=state["memory_context"],
            preferences=state["preference_context"],
            graph_recommendations=state["graph_recommendations"],
            reasoning=state["reasoning_context"],
            explanation_context=state.get("explanation_context", ""),
            intent=state["content"],
        )
        by_id = {track["id"]: track for track in candidates}
        recommended = [by_id[track_id] for track_id in plan.track_ids if track_id in by_id]
        rationale = plan.rationale
        if not plan.used_gemini:
            rationale = await self.graph_client.fallback_explanation(
                recommendations=recommended, preferences=state["preference_context"],
                reasoning=state["reasoning_context"], user_id=state["user_id"],
            )
        print(f"Recommendation plan: {plan.track_ids} (used Gemini: {plan.used_gemini})")
        return {
            "recommended": recommended,
            "recommendation_reason": rationale,
            "gemini_recommendation_used": plan.used_gemini,
        }

    @staticmethod
    async def compose_reply(state: ChatWorkflowState) -> dict[str, Any]:
        print(f"Composing reply for {len(state['recommended'])} recommended tracks (Gemini used: {state['gemini_recommendation_used']})")
        reply = state["turn"].reply
        if state["signals"] and state["recommended"]:
            reply += "\n\nTry: " + ", ".join(
                f"{track['title']} — {track['artistName']}" for track in state["recommended"]
            )
        if state.get("recommendation_reason"):
            reply += f"\n\nWhy these: {state['recommendation_reason']}"
        return {"reply_content": reply}
