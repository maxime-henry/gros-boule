### Project Snapshot
- Streamlit multi-page app for daily squat challenge; entrypoint [app.py](app.py) plus analytics in [pages/](pages).
- UI is in French, keep playful tone and emoji-heavy microcopy when extending components.
### Running & Env
- Launch locally with `streamlit run app.py`; Streamlit auto-detects extra pages under [pages/](pages).
- Place `.env` with `ACCESS_KEY`, `SECRET_ACCESS_KEY`, `MISTRAL_API_KEY`; `config.load_dotenv()` loads them before boto3/Mistral init.
- DynamoDB table name is hard-coded to `squats`; confirm the table exists in `eu-central-1` before hacking on data fetches.
- Time logic uses UTC+1 offsets via `today = datetime.now()+timedelta(hours=1)` in [config.py](config.py); keep consistency when adding new timestamps.
### Data Model & Helpers
- Persist squats via `save_new_squat(name, squats_count)` which stores ISO timestamps and immediately writes through boto3; reuse it instead of manual boto calls.
- `load_all()` returns the current-year slice as pandas DataFrame; downstream code expects `date` already parsed to `datetime`.
- `today_data()` is the lightweight filter when you only need today's entries; prefer it over manual masking.
- `Participant` objects (instantiated in [app.py](app.py) and reused in tabs) encapsulate rolling stats such as `delta_done_vs_objecitf_today`, yesterday totals, and per-day averages—extend that class instead of duplicating math.
### Main Page Patterns
- Participant order is mutated by cookie `id_squatteur`; respect the cookie round-trip managed by `streamlit_cookies_controller.CookieController` before reordering tabs.
- When handling form submissions, update `squat_data`, rebuild the relevant `Participant`, then optionally `st.rerun()` to refresh metrics—see the tab loop in [app.py](app.py).
- Motivational copy pulls from [motivation.py](motivation.py) and Mistral; call `mistral_chat()` sparingly and guard it with fallbacks like the existing `try/except`.
### Stats & Data Pages
- [pages/1_📈_Stats.py](pages/1_%F0%9F%93%88_Stats.py) recomputes derived tables (daily sums, cumulative curves, correlation heatmap); it drops `Tonix` unless the checkbox is enabled—keep that UX quirk.
- Lot of metrics rely on `filtered_df` (first non-zero day per participant) and `daily_squats`; if you add visuals, derive from those to stay consistent.
- [pages/2_📋_Data.py](pages/2_%F0%9F%93%8B_Data.py) is intentionally raw: it shows the sorted DataFrame plus headline counts; don't add heavy plots there—leave deep viz to the Stats tab.
### UX Conventions
- Tone is half-motivational, half-taunting; new copy should stay informal, emoji-laden, and bilingual French/English as in current strings.
- Metrics and charts typically pin the daily target line at 20 squats; reuse the same red reference line so readers instantly see progress.
- Keep layout lean: `st.set_page_config(... initial_sidebar_state='collapsed')` is everywhere, so avoid widgets that require the sidebar.
### Integrations & Safety
- Cookies expire after ~5 days; if you add new cookies, align expiry with the existing pattern to avoid user surprise.
- Mistral agent ID is in-source; never log raw API responses or keys, and prefer environment variables for anything new.
- The boto3 resource is module-level; avoid creating additional clients in hot code paths—import from [config.py](config.py) instead.
### When Adding Features
- Always thread new participant stats through the `Participant` class so tabs, motivational prompts, and analytics stay in sync.
- For new plots, convert `date` to `date_day` before grouping to match existing figures and avoid timezone drift.
- If you need aggregate numbers elsewhere, consider memoizing `load_all()` with `st.cache_data` (currently not cached) but be mindful of real-time updates after form submissions.
