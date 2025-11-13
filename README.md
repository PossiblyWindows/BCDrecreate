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

On top of the automation improvements, the GUI now delivers 283 interface-level features, bringing the combined total to 335 capabilities:

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

### Advanced GUI catalogue

127. Prefix toggle: millisecond timestamps in the log viewer.
128. Prefix toggle: HH:MM:SS timestamps.
129. Prefix toggle: YYYY-MM-DD date stamps.
130. Prefix toggle: weekday labels for each entry.
131. Prefix toggle: ISO8601 timestamps.
132. Prefix toggle: delta from the previous log line.
133. Prefix toggle: elapsed time since the first captured log.
134. Prefix toggle: sequential log numbering.
135. Prefix toggle: emitting thread name.
136. Prefix toggle: emitting thread identifier.
137. Prefix toggle: log level banner.
138. Prefix toggle: primary keyword label.
139. Prefix toggle: active language code.
140. Prefix toggle: beta state summary (on/off with counts).
141. Suffix toggle: message length characters.
142. Suffix toggle: message word count.
143. Suffix toggle: total character count.
144. Suffix toggle: digit sum indicator.
145. Suffix toggle: numeric token echo.
146. Suffix toggle: points estimate accumulator.
147. Suffix toggle: keyword match count.
148. Suffix toggle: rendered index number.
149. Suffix toggle: elapsed minutes since the first entry.
150. Suffix toggle: elapsed seconds since the first entry.
151. Suffix toggle: thread marker suffix.
152. Suffix toggle: short hash fingerprint.
153. Suffix toggle: cycle marker flag.
154. Suffix toggle: summary pointer badge.
155. Transform toggle: uppercase error lines.
156. Transform toggle: uppercase warning lines.
157. Transform toggle: lowercase informational lines.
158. Transform toggle: title-case formatter.
159. Transform toggle: highlight numeric tokens.
160. Transform toggle: emphasise tracked keywords inline.
161. Transform toggle: rename “points” to “pts”.
162. Transform toggle: pad bracketed expressions.
163. Transform toggle: collapse repeated whitespace.
164. Transform toggle: indent multi-line entries.
165. Transform toggle: bullet prefix decoration.
166. Transform toggle: capitalise the first character.
167. Wrapper toggle: surround entries with brackets.
168. Wrapper toggle: surround entries with « » chevrons.
169. Wrapper toggle: surround entries with pipes.
170. Wrapper toggle: surround entries with stars.
171. Wrapper toggle: surround entries with box-drawing glyphs.
172. Wrapper toggle: surround entries with wave markers.
173. Filter toggle: show only errors and warnings.
174. Filter toggle: show strictly errors.
175. Filter toggle: show only warnings.
176. Filter toggle: hide informational lines.
177. Filter toggle: hide success completions.
178. Filter toggle: hide ChatGPT chatter.
179. Filter toggle: hide license updates.
180. Filter toggle: hide prefetch telemetry.
181. Filter toggle: hide cycle markers.
182. Filter toggle: hide duplicate messages.
183. Action toggle: audio alert on errors.
184. Action toggle: audio alert on warnings.
185. Action toggle: audio alert on cycle markers.
186. Action toggle: copy errors to clipboard automatically.
187. Action toggle: copy ChatGPT replies to clipboard.
188. Action toggle: copy completion lines to clipboard.
189. Action toggle: focus the GUI when errors appear.
190. Action toggle: pause log intake on errors.
191. Action toggle: clear the log when a new cycle begins.
192. Action toggle: enable wrapping for very long messages.
193. Layout toggle: expand the log panel height.
194. Layout toggle: compact panel padding.
195. Layout toggle: bolden section headers.
196. Layout toggle: widen control buttons.
197. Layout toggle: highlight the beta panel.
198. Layout toggle: highlight the advanced panel.
199. Layout toggle: highlight the log panel background.
200. Layout toggle: round the control frames.
201. Layout toggle: dim panel backgrounds.
202. Layout toggle: flatten the control buttons.
203. Summary toggle: show total log lines.
204. Summary toggle: show error count.
205. Summary toggle: show warning count.
206. Summary toggle: show info count.
207. Summary toggle: last message snippet.
208. Summary toggle: last error snippet.
209. Summary toggle: last warning snippet.
210. Summary toggle: last highlighted keyword.
211. Summary toggle: GPT mention counter.
212. Summary toggle: cycle mention counter.
213. Summary toggle: task mention counter.
214. Summary toggle: subject mention counter.
215. Summary toggle: retry mention counter.
216. Summary toggle: skip mention counter.
217. Summary toggle: prefetch mention counter.
218. Summary toggle: license mention counter.
219. Summary toggle: total numeric points.
220. Summary toggle: log duration span.
221. Summary toggle: average message length.
222. Summary toggle: unique keyword counter.
223. Summary toggle: completion mention counter.
224. Highlight toggle: Login flow events.
225. Highlight toggle: Cookie banner handling.
226. Highlight toggle: ChatGPT interactions.
227. Highlight toggle: Subject picks.
228. Highlight toggle: Topic picks.
229. Highlight toggle: Task flow.
230. Highlight toggle: Points notices.
231. Highlight toggle: Top score updates.
232. Highlight toggle: Skip tracking.
233. Highlight toggle: Retry notices.
234. Highlight toggle: Cycle changes.
235. Highlight toggle: License chatter.
236. Highlight toggle: Trial messaging.
237. Highlight toggle: Debug output.
238. Highlight toggle: Completion confirmations.
239. Highlight toggle: Submission states.
240. Highlight toggle: Cookie declines.
241. Highlight toggle: HTTP diagnostics.
242. Highlight toggle: Prefetch telemetry.
243. Highlight toggle: Remote probe notes.
244. Highlight toggle: Driver status.
245. Highlight toggle: Chrome lifecycle.
246. Highlight toggle: Session changes.
247. Highlight toggle: Metrics analysis.
248. Highlight toggle: Summary emissions.
249. Highlight toggle: Dropdown handling.
250. Highlight toggle: Input field handling.
251. Highlight toggle: Selection handling.
252. Highlight toggle: Submit handling.
253. Highlight toggle: Automation status.
254. Highlight toggle: Cache management.
255. Highlight toggle: Probe diagnostics.
256. Highlight toggle: Radix overlay handling.
257. Highlight toggle: Watchdog resets.
258. Highlight toggle: Parallelism logs.
259. Highlight toggle: Queue status.
260. Highlight toggle: Thread markers.
261. Highlight toggle: Restart notices.
262. Highlight toggle: Rebuild notices.
263. Highlight toggle: Sync activity.
264. Highlight toggle: Filter adjustments.
265. Highlight toggle: Highlight adjustments.
266. Highlight toggle: Export operations.
267. Highlight toggle: Import operations.
268. Highlight toggle: Preset management.
269. Highlight toggle: Credential operations.
270. Highlight toggle: Beta lifecycle.
271. Highlight toggle: Feature toggles.
272. Highlight toggle: Until-target tracking.
273. Highlight toggle: Gain tracking.
274. Filter toggle: show only Login flow lines.
275. Filter toggle: show only Cookie banner lines.
276. Filter toggle: show only ChatGPT lines.
277. Filter toggle: show only Subject pick lines.
278. Filter toggle: show only Topic pick lines.
279. Filter toggle: show only Task flow lines.
280. Filter toggle: show only Points lines.
281. Filter toggle: show only Top score lines.
282. Filter toggle: show only Skip lines.
283. Filter toggle: show only Retry lines.
284. Filter toggle: show only Cycle lines.
285. Filter toggle: show only License lines.
286. Filter toggle: show only Trial lines.
287. Filter toggle: show only Debug lines.
288. Filter toggle: show only Completion lines.
289. Filter toggle: show only Submission lines.
290. Filter toggle: show only Cookie decline lines.
291. Filter toggle: show only HTTP lines.
292. Filter toggle: show only Prefetch lines.
293. Filter toggle: show only Remote probe lines.
294. Filter toggle: show only Driver lines.
295. Filter toggle: show only Chrome lines.
296. Filter toggle: show only Session lines.
297. Filter toggle: show only Metrics lines.
298. Filter toggle: show only Summary lines.
299. Filter toggle: show only Dropdown lines.
300. Filter toggle: show only Input lines.
301. Filter toggle: show only Selection lines.
302. Filter toggle: show only Submit lines.
303. Filter toggle: show only Automation lines.
304. Filter toggle: show only Cache lines.
305. Filter toggle: show only Probe lines.
306. Filter toggle: show only Radix lines.
307. Filter toggle: show only Watchdog lines.
308. Filter toggle: show only Parallelism lines.
309. Filter toggle: show only Queue lines.
310. Filter toggle: show only Thread lines.
311. Filter toggle: show only Restart lines.
312. Filter toggle: show only Rebuild lines.
313. Filter toggle: show only Sync lines.
314. Filter toggle: show only Filter-change lines.
315. Filter toggle: show only Highlight-change lines.
316. Filter toggle: show only Export lines.
317. Filter toggle: show only Import lines.
318. Filter toggle: show only Preset lines.
319. Filter toggle: show only Credential lines.
320. Filter toggle: show only Beta lifecycle lines.
321. Filter toggle: show only Feature toggle lines.
322. Filter toggle: show only Until-target lines.
323. Filter toggle: show only Gain tracking lines.
324. Highlight toggle: Performance updates.
325. Highlight toggle: Stability notices.
326. Highlight toggle: Interface adjustments.
327. Highlight toggle: Theme tweaks.
328. Highlight toggle: History entries.
329. Highlight toggle: Overview summaries.
330. Filter toggle: show only Performance lines.
331. Filter toggle: show only Stability lines.
332. Filter toggle: show only Interface lines.
333. Filter toggle: show only Theme lines.
334. Filter toggle: show only History lines.
335. Filter toggle: show only Overview lines.
