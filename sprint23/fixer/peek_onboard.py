"""Show lines 14970-15020 (showWelcomePrompt trigger) and 15495-15560 (onboarding Escape
handler) in CURRENT file."""
cur = open('/root/backyard-designer/index.html').read().split('\n')
for rng in ((14970, 15020), (15495, 15565)):
    print(f'===== lines {rng[0]}-{rng[1]} =====')
    for i in range(rng[0], rng[1]):
        print(i, cur[i - 1][:115])