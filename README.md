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

The beta flag now unlocks 52 optimisations and quality-of-life upgrades:

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

All beta statistics are printed once the run finishes so you can quickly gauge how many tasks were solved, total points gained,
skips, Top gain, and which user ID was active.
