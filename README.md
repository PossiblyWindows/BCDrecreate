# Windows Boot Repair Script

This batch script is designed to repair Windows boot configuration and restore bootability using `bcdedit` and `bcdboot`.

## Features

- **Backup BCD**: Creates a backup of the Boot Configuration Data (BCD) before making any changes.
- **Repair BCD**: Repairs the Boot Configuration Data (BCD) to fix boot-related issues.
- **Restore Boot Files**: Restores boot files to ensure Windows boots properly.
- **Reverse Delete Operation**: Reverses the effects of `BCDEDIT /delete {current}` by restoring the deleted boot entry.
- **Menu**: Provides a menu interface for easy selection of individual operations or an "All-in-One" option to perform all operations sequentially.

## Usage

1. Clone or download the script.
2. Run the script with administrative privileges (right-click > Run as administrator).
3. Select an option from the menu to perform the desired operation.
4. Follow the on-screen instructions if any errors occur.

## Disclaimer

- Use this script at your own risk. Modifying boot configuration data can have serious consequences if not done correctly.
- Always ensure you have backups of important data before making changes to the boot configuration.
- The script is provided as-is without any warranties.

## License

This project is licensed under the [MIT License](LICENSE).

---

## Uzdevumi.lv Automation Bot

The repository also ships a Python automation helper (`uzdevumi_bot.py`) that drives Chrome with Selenium/undetected-chromedriver to speed through Uzdevumi.lv tasks. A GUI is available when `customtkinter` is installed, or you can run it fully in CLI mode.

### Quick start

```bash
python uzdevumi_bot.py --nogui --user <ID> --passw <PASSWORD>
```

Optional flags:

- `--lang {lv,en,ru}` – switch logging and prompts.
- `--until-top` / `--gain` – stop after reaching a target Top score.
- `--license-user` / `--license` – provide Keysys credentials.
- `--beta` – enable the experimental, faster beta build.

### Beta mode highlights

The beta flag unlocks 52 automation optimisations and quality-of-life upgrades:

1. Cached translations to avoid repeating string lookups.
2. Pre-compiled regular expressions for parsing answers and points.
3. Subject catalog caching to skip redundant DOM scraping.
4. Cookie guard that declines banners only once per domain.
5. Hardened Chrome launch options that mute background work.
6. Tighter Selenium waits for faster element resolution.
7. Adaptive ChatGPT session refresh cadence.
8. Cached prompt headers to shrink browser DOM mutations.
9. Smarter answer parsing with extra fallbacks.
10. Dropdown selection guards that clamp out-of-range values.
11. Normalised text inputs before submission.
12. Structured timestamped logging.
13. Automatic recovery backoff on driver rebuilds.
14. Session metrics with an end-of-run beta summary.
15. Subject rotation to avoid repeating the same topic.
16. Enhanced Top-point tracking in the metrics report.
17. Credential memory (user ID only) recorded in the summary.
18. Safer submit-button handling across answer modes.
19. Automatic skipping of zero-point tasks.
20. Background subject prefetching for subsequent cycles.
21. Parallel HTTP task prefetcher that screens potential exercises concurrently.
22. Remote media probe that rejects image-heavy tasks before loading them in the browser.
23. High-value (>3 point) smart retry loop with fresh ChatGPT answers after refreshes.
24. Submission feedback scanner that checks for correct/incorrect cues in the DOM.
25. Prompt variation on retries to coax alternative GPT responses.
26. ChatGPT Radix overlay click support for selectors `_r_10_` and `_r_19_`.
27. ChatGPT session watchdog that rebuilds the driver if the tab disappears.
28. Send-button retry guard that ensures each message actually posts.
29. Browser-cookie synchronisation so remote HTTP probes stay authenticated.
30. User-agent hint injection for consistent upstream requests.
31. Detailed prefetch logging that reports how many tasks were skipped before loading.
32. Dropdown resilience that re-acquires stale `<select>` elements automatically.
33. Textual-response tokeniser for free-form answer parsing.
34. Numeric normaliser that unifies decimal separators for text answers.
35. Answer-mode detection that routes between text, dropdown, and choice fillers.
36. Submission feedback analytics fed back into the beta metrics log.
37. Top snapshot history that records the starting and current Top score.
38. Task skip counter that records remotely filtered exercises.
39. Retry prompt backoff that escalates only when feedback stays incorrect.
40. Parallel executor pool tuned specifically for the HTTP probe workload.
41. HTTP probe timeout guards that keep the prefetch ultra fast.
42. Radix resilience that handles evolving ChatGPT UI anchors without breaking.
43. Page refresh guard that reapplies the media-hiding stylesheet after retries.
44. Task summary logging so every prompt includes a concise textual preview.
45. UI placeholder sync that localises GUI hints live as you change languages.
46. License status polling in the GUI to avoid blocking the start button.
47. Credential vault integration for optional secure credential reuse.
48. Remote probe fallback that gracefully continues if every task contains media.
49. Task loop metrics covering tasks solved, points scored, and skip counts.
50. Scoped logging hooks that keep beta telemetry flowing into the GUI console.
51. Automation health checks that keep the run alive after transient driver errors.
52. Smart sleep reduction to keep the overall loop snappy without overloading the site.

### GUI control suite

On top of the automation improvements, the GUI now delivers another 74 interface-level features, bringing the combined total to 126 capabilities:

53. Theme switcher (system / light / dark appearance modes).
54. Accent colour picker with blue, dark-blue, green, teal, red, purple, and orange presets.
55. UI scaling slider to resize the entire window without restarting the app.
56. Log font-size slider to tune readability on the fly.
57. Log line-wrap toggle for wide messages.
58. Log auto-scroll toggle to freeze the view when you are reviewing output.
59. Pause/resume control that buffers log messages until you unpause.
60. Error and warning highlight toggle for instant visual cues.
61. Timestamp toggle for every log line.
62. Log filter search box to show only matching messages.
63. One-click log clearing.
64. Clipboard copy of the filtered log view.
65. Save-to-disk support for text or JSON log exports.
66. Instant localisation refresh so placeholders and labels follow the chosen language.
67. Beta feature search to filter the long toggle list.
68. Enable-all beta toggles button.
69. Disable-all beta toggles button.
70. Restore-default beta toggle states.
71. Import beta presets from JSON.
72. Export beta presets to JSON.
73. Collapsible beta panel to reclaim space when you do not need it.
74. Live beta feature counter showing how many optimisations remain enabled.
75. Toggle: Cache translations.
76. Toggle: Reuse compiled regexes.
77. Toggle: Cache subject catalog.
78. Toggle: Decline cookie banners once.
79. Toggle: Accelerated Chrome launch flags.
80. Toggle: Faster Selenium waits.
81. Toggle: Adaptive ChatGPT refresh cadence.
82. Toggle: Cached prompt headers.
83. Toggle: Extra answer parsing fallbacks.
84. Toggle: Dropdown guardrails.
85. Toggle: Normalise text inputs.
86. Toggle: Structured beta logging.
87. Toggle: Beta metrics reporting.
88. Toggle: Driver recovery backoff.
89. Toggle: Subject rotation.
90. Toggle: Enhanced Top tracking.
91. Toggle: Remember credential user ID.
92. Toggle: Safe submit button handling.
93. Toggle: Skip zero-point tasks.
94. Toggle: Subject prefetch cache.
95. Toggle: Parallel HTTP prefetch.
96. Toggle: Remote media probe.
97. Toggle: High-value smart retry.
98. Toggle: Submission feedback scanner.
99. Toggle: Prompt variation on retries.
100. Toggle: Radix overlay auto-click.
101. Toggle: ChatGPT session watchdog.
102. Toggle: Send-button retry guard.
103. Toggle: Sync cookies to the HTTP client.
104. Toggle: User-Agent hints for probes.
105. Toggle: Prefetch telemetry logging.
106. Toggle: Re-acquire stale dropdowns.
107. Toggle: Tokenize free-form answers.
108. Toggle: Unify decimal separators.
109. Toggle: Auto answer-mode detection.
110. Toggle: Feedback analytics.
111. Toggle: Top snapshot history.
112. Toggle: Skip counter.
113. Toggle: Retry prompt backoff.
114. Toggle: Dedicated executor pool.
115. Toggle: HTTP probe timeouts.
116. Toggle: Radix selector resilience.
117. Toggle: Reapply CSS after refresh.
118. Toggle: Task summary logging.
119. Toggle: Live placeholder localisation.
120. Toggle: GUI license polling.
121. Toggle: Credential vault integration.
122. Toggle: Fallback when probes fail.
123. Toggle: Task loop metrics.
124. Toggle: Scoped logging hooks.
125. Toggle: Automation health checks.
126. Toggle: Reduced sleep delays.

All beta statistics are printed once the run finishes so you can quickly gauge how many tasks were solved, total points gained,
skips, Top gain, and which user ID was active.
