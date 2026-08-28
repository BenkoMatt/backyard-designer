"""V13 diag: my test data has params:{} — loadDesign FILTERS OUT objects with
falsy/empty params! `if (!obj.params || typeof obj.params !== 'object') return false;`
{} is truthy so that passes... wait {} is truthy. So filter passes. Then what
removed id 7 entirely? The dup-scan: seenIds 7 -> dup -> droppedDupes=1, 8 kept.
maxLoadedId=8. nextId=9. Load loop: id7 bush (first, passes has-check), id7 hedge
(SKIPPED), id8 tree. count should be 2!

Result shows count=1 with only id 8. So id 7 bush ALSO got dropped. Why?
sanitizeObjectParams(bush_round, {}) -> obj.params={} is truthy object ->
sanitized = {} then catalog loop fills defaults... then extra-keys loop. Returns
defaults. Not null. Hmm.

Wait — maybe CATALOG[bush_round] doesn't exist! My test types: bush_round,
hedge_formal, tree_deciduous. The first object got dropped at the CATALOG check
(`if (!CATALOG[migratedType]) return null`) — meaning bush_round isn't a real type!

diag23 result types: only tree_deciduous survived. So bush_round AND hedge_formal
aren't catalog types (or one of them). Use REAL catalog types. Check the lib-item
types used elsewhere: earlier tests used .lib-item clicks (which use real types).
Grab three real type names from the catalog.