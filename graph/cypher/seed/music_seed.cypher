// ============================================================
// Sample artists / albums / tracks + how they relate to each other.
// (Artist)-[:RELEASED]->(Album)-[:CONTAINS]->(Track)
// (Artist)-[:PERFORMED]->(Track)
// Enough variety here (4 artists, 5 albums, 12 tracks) to make
// recommendation/collaborative-filtering queries produce real results
// once interactions_seed.cypher is loaded on top.
// ============================================================

// -- artists ---------------------------------------------------------
MERGE (ar1:Artist {artist_id: 'artist_001'})
SET ar1.name = 'Tame Impala', ar1.genres = ['psychedelic rock', 'synth-pop'];

MERGE (ar2:Artist {artist_id: 'artist_002'})
SET ar2.name = 'Daft Punk', ar2.genres = ['electronic', 'house'];

MERGE (ar3:Artist {artist_id: 'artist_003'})
SET ar3.name = 'Billie Eilish', ar3.genres = ['pop', 'alternative'];

MERGE (ar4:Artist {artist_id: 'artist_004'})
SET ar4.name = 'Kendrick Lamar', ar4.genres = ['hip hop', 'rap'];

// -- albums -----------------------------------------------------
MERGE (al1:Album {album_id: 'album_001'})
SET al1.title = 'Currents', al1.release_year = 2015;

MERGE (al2:Album {album_id: 'album_002'})
SET al2.title = 'Random Access Memories', al2.release_year = 2013;

MERGE (al3:Album {album_id: 'album_003'})
SET al3.title = 'The Slow Rush', al3.release_year = 2020;

MERGE (al4:Album {album_id: 'album_004'})
SET al4.title = 'Happier Than Ever', al4.release_year = 2021;

MERGE (al5:Album {album_id: 'album_005'})
SET al5.title = 'DAMN.', al5.release_year = 2017;

// -- tracks -----------------------------------------------------
MERGE (t1:Track {track_id: 'track_001'})
SET t1.title = 'The Less I Know the Better', t1.duration_ms = 216320, t1.genre = 'psychedelic rock';

MERGE (t2:Track {track_id: 'track_002'})
SET t2.title = 'Let It Happen', t2.duration_ms = 467000, t2.genre = 'psychedelic rock';

MERGE (t3:Track {track_id: 'track_003'})
SET t3.title = 'Get Lucky', t3.duration_ms = 369000, t3.genre = 'funk';

MERGE (t4:Track {track_id: 'track_004'})
SET t4.title = 'One More Time', t4.duration_ms = 320000, t4.genre = 'house';

MERGE (t5:Track {track_id: 'track_005'})
SET t5.title = 'Instant Crush', t5.duration_ms = 337000, t5.genre = 'electronic';

MERGE (t6:Track {track_id: 'track_006'})
SET t6.title = 'Borderline', t6.duration_ms = 213000, t6.genre = 'psychedelic rock';

MERGE (t7:Track {track_id: 'track_007'})
SET t7.title = 'Lost in Yesterday', t7.duration_ms = 233000, t7.genre = 'psychedelic rock';

MERGE (t8:Track {track_id: 'track_008'})
SET t8.title = 'Happier Than Ever', t8.duration_ms = 298000, t8.genre = 'alternative';

MERGE (t9:Track {track_id: 'track_009'})
SET t9.title = 'Therefore I Am', t9.duration_ms = 174000, t9.genre = 'pop';

MERGE (t10:Track {track_id: 'track_010'})
SET t10.title = 'HUMBLE.', t10.duration_ms = 177000, t10.genre = 'hip hop';

MERGE (t11:Track {track_id: 'track_011'})
SET t11.title = 'DNA.', t11.duration_ms = 185000, t11.genre = 'hip hop';

MERGE (t12:Track {track_id: 'track_012'})
SET t12.title = 'LOYALTY. FEAT. RIHANNA.', t12.duration_ms = 234000, t12.genre = 'hip hop';

// -- Artist -[:RELEASED]-> Album -----------------------------------------------------
WITH 1 AS _
MATCH (ar1:Artist {artist_id: 'artist_001'}), (al1:Album {album_id: 'album_001'})
MERGE (ar1)-[:RELEASED]->(al1);

WITH 1 AS _
MATCH (ar1:Artist {artist_id: 'artist_001'}), (al3:Album {album_id: 'album_003'})
MERGE (ar1)-[:RELEASED]->(al3);

WITH 1 AS _
MATCH (ar2:Artist {artist_id: 'artist_002'}), (al2:Album {album_id: 'album_002'})
MERGE (ar2)-[:RELEASED]->(al2);

WITH 1 AS _
MATCH (ar3:Artist {artist_id: 'artist_003'}), (al4:Album {album_id: 'album_004'})
MERGE (ar3)-[:RELEASED]->(al4);

WITH 1 AS _
MATCH (ar4:Artist {artist_id: 'artist_004'}), (al5:Album {album_id: 'album_005'})
MERGE (ar4)-[:RELEASED]->(al5);

// -- Album -[:CONTAINS]-> Track -----------------------------------------------------
WITH 1 AS _
MATCH (al1:Album {album_id: 'album_001'}), (t1:Track {track_id: 'track_001'})
MERGE (al1)-[:CONTAINS]->(t1);

WITH 1 AS _
MATCH (al1:Album {album_id: 'album_001'}), (t2:Track {track_id: 'track_002'})
MERGE (al1)-[:CONTAINS]->(t2);

WITH 1 AS _
MATCH (al2:Album {album_id: 'album_002'}), (t3:Track {track_id: 'track_003'})
MERGE (al2)-[:CONTAINS]->(t3);

WITH 1 AS _
MATCH (al2:Album {album_id: 'album_002'}), (t4:Track {track_id: 'track_004'})
MERGE (al2)-[:CONTAINS]->(t4);

WITH 1 AS _
MATCH (al2:Album {album_id: 'album_002'}), (t5:Track {track_id: 'track_005'})
MERGE (al2)-[:CONTAINS]->(t5);

WITH 1 AS _
MATCH (al3:Album {album_id: 'album_003'}), (t6:Track {track_id: 'track_006'})
MERGE (al3)-[:CONTAINS]->(t6);

WITH 1 AS _
MATCH (al3:Album {album_id: 'album_003'}), (t7:Track {track_id: 'track_007'})
MERGE (al3)-[:CONTAINS]->(t7);

WITH 1 AS _
MATCH (al4:Album {album_id: 'album_004'}), (t8:Track {track_id: 'track_008'})
MERGE (al4)-[:CONTAINS]->(t8);

WITH 1 AS _
MATCH (al4:Album {album_id: 'album_004'}), (t9:Track {track_id: 'track_009'})
MERGE (al4)-[:CONTAINS]->(t9);

WITH 1 AS _
MATCH (al5:Album {album_id: 'album_005'}), (t10:Track {track_id: 'track_010'})
MERGE (al5)-[:CONTAINS]->(t10);

WITH 1 AS _
MATCH (al5:Album {album_id: 'album_005'}), (t11:Track {track_id: 'track_011'})
MERGE (al5)-[:CONTAINS]->(t11);

WITH 1 AS _
MATCH (al5:Album {album_id: 'album_005'}), (t12:Track {track_id: 'track_012'})
MERGE (al5)-[:CONTAINS]->(t12);

// -- Artist -[:PERFORMED]-> Track -----------------------------------------------------
WITH 1 AS _
MATCH (ar1:Artist {artist_id: 'artist_001'}), (t1:Track {track_id: 'track_001'})
MERGE (t1)-[:BY]->(ar1);

WITH 1 AS _
MATCH (ar1:Artist {artist_id: 'artist_001'}), (t2:Track {track_id: 'track_002'})
MERGE (t2)-[:BY]->(ar1);

WITH 1 AS _
MATCH (ar1:Artist {artist_id: 'artist_001'}), (t6:Track {track_id: 'track_006'})
MERGE (t6)-[:BY]->(ar1);

WITH 1 AS _
MATCH (ar1:Artist {artist_id: 'artist_001'}), (t7:Track {track_id: 'track_007'})
MERGE (t7)-[:BY]->(ar1);

WITH 1 AS _
MATCH (ar2:Artist {artist_id: 'artist_002'}), (t3:Track {track_id: 'track_003'})
MERGE (t3)-[:BY]->(ar2);

WITH 1 AS _
MATCH (ar2:Artist {artist_id: 'artist_002'}), (t4:Track {track_id: 'track_004'})
MERGE (t4)-[:BY]->(ar2);

WITH 1 AS _
MATCH (ar2:Artist {artist_id: 'artist_002'}), (t5:Track {track_id: 'track_005'})
MERGE (t5)-[:BY]->(ar2);

WITH 1 AS _
MATCH (ar3:Artist {artist_id: 'artist_003'}), (t8:Track {track_id: 'track_008'})
MERGE (t8)-[:BY]->(ar3);

WITH 1 AS _
MATCH (ar3:Artist {artist_id: 'artist_003'}), (t9:Track {track_id: 'track_009'})
MERGE (t9)-[:BY]->(ar3);

WITH 1 AS _
MATCH (ar4:Artist {artist_id: 'artist_004'}), (t10:Track {track_id: 'track_010'})
MERGE (t10)-[:BY]->(ar4);

WITH 1 AS _
MATCH (ar4:Artist {artist_id: 'artist_004'}), (t11:Track {track_id: 'track_011'})
MERGE (t11)-[:BY]->(ar4);

WITH 1 AS _
MATCH (ar4:Artist {artist_id: 'artist_004'}), (t12:Track {track_id: 'track_012'})
MERGE (t12)-[:BY]->(ar4);
