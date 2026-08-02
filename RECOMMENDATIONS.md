# Using the Recommendation Service

`graph.services.recommendation_service.RecommendationService` reads the
listening graph in Neo4j and returns plain Python dictionaries. It has three
heuristic strategies:

- `collaborative`: tracks played by listeners with overlapping play history.
- `by_artist_affinity`: unplayed tracks by artists the user has already played.
- `by_genre_affinity`: unplayed tracks in genres the user has already played.

All three exclude tracks the target user has already played. An unknown user,
or a user without enough history for a strategy, returns an empty list.

## 1. Configure Neo4j

From the project root:

```bash
cp .env.example .env
```

Set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, and, if necessary,
`NEO4J_DATABASE` in `.env`. Start the Neo4j database before proceeding.

Install dependencies and load the included data set:

```bash
venv/bin/pip install -r requirements.txt
venv/bin/python -m graph.builders.graph_builder --schema --seed
```

The seed data includes `user_001`, which has sufficient history to demonstrate
all recommendation strategies.

## 2. Run it from the command line

Run every strategy for a user:

```bash
venv/bin/python -m graph.builders.recommendation_cli user_001 --strategy all --limit 5
```

Run one strategy:

```bash
venv/bin/python -m graph.builders.recommendation_cli user_001 --strategy collaborative --limit 10
venv/bin/python -m graph.builders.recommendation_cli user_001 --strategy artist --limit 10
venv/bin/python -m graph.builders.recommendation_cli user_001 --strategy genre --limit 10
```

The command writes JSON to standard output; when `--strategy all` is used,
results are grouped under `collaborative`, `artist`, and `genre`.

## 3. Call it from Python

```python
from graph.services.recommendation_service import RecommendationService

recommendations = RecommendationService()

collaborative = recommendations.collaborative("user_001", limit=10)
artist_affinity = recommendations.by_artist_affinity("user_001", limit=10)
genre_affinity = recommendations.by_genre_affinity("user_001", limit=10)

print(collaborative)
```

Run the script from the project root so `graph` is importable. The service
returns a list of dictionaries. The fields differ slightly by strategy:

- collaborative: `track_id`, `title`, `shared_listeners`
- artist: `track_id`, `title`, `artist`, `affinity`
- genre: `track_id`, `title`, `genre`, `genre_affinity`

## 4. Use it through MCP (optional)

The MCP server exposes the same service as these tools:

- `recommend_collaborative(user_id, limit=10)`
- `recommend_by_artist_affinity(user_id, limit=10)`
- `recommend_by_genre_affinity(user_id, limit=10)`

Start it with:

```bash
venv/bin/python -m spotify_mcp
```

Configure your MCP client to run that command with this repository as its
working directory. The server uses stdio by default.
