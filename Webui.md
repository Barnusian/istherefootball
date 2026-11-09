# Football Fixtures: Weekly Forecast Website

## Project Overview

Extend the existing football fixtures project to include a simple web interface displaying two weekly fixture reports: **This Week** and **Next Week**.

The visual concept is an old-school sports information terminal, inspired by 1980s/1990s computing, Teletext and retro sports databases.

The website should feel more like a digital noticeboard than a conventional website. Its main feature will be two images resembling printed thermal receipts, displayed side by side against a black background.

Before making changes, inspect the existing project, understand its data generation, printing and scheduling workflows, and preserve existing functionality wherever possible.

## 1. Existing Functionality

The project currently:

- Retrieves football fixtures from ICS sources.
- Processes fixtures relating to Rangers, Celtic and Scotland.
- Generates two JSON outputs:
  - **Long:** Contains fixtures across the entire date range provided by the ICS sources.
  - **Short:** Contains a weekly forecast.
- Runs automatically on Mondays, approximately 08:00–09:00.
- Prints the short weekly forecast using the existing thermal printer daemon.

Retain the existing fixture filtering, data structures and printing functionality unless changes are necessary to support the new requirements.

## 2. Revised Weekly Generation

The existing weekly generation needs extending to produce two distinct weekly forecasts.

On the scheduled Monday run:

1. Retrieve and process the ICS fixture data using the existing logic.
2. Generate the full-range JSON output, retaining its existing purpose.
3. Generate a **This Week** forecast, covering Monday to Sunday of the current week.
4. Generate a **Next Week** forecast, covering Monday to Sunday of the following week.
5. Generate a PNG receipt image for each weekly forecast.
6. Print the This Week report using the existing thermal printer daemon.

Next Week must be generated and saved but must NOT be printed automatically.

### Date handling

- Weeks run Monday to Sunday.
- Use the system's local date when determining the current week.
- Calculate both weekly date ranges dynamically; do not hardcode dates.
- Include fixtures only when their dates fall within the relevant Monday–Sunday range, inclusive.
- Ensure the logic works correctly across month boundaries, year boundaries and leap years.
- Both forecasts should be generated from the same retrieved and processed ICS dataset to avoid inconsistent results.

### JSON outputs and filenames

Review the existing filenames and update them to clearly distinguish the different datasets.

Use descriptive naming that incorporates the concepts of `this-week` and `next-week`.

The resulting outputs should distinguish:

- Full ICS date-range data.
- This week's weekly forecast.
- Next week's weekly forecast.

Update all references to the renamed files, including the printing script, scheduled jobs and any other dependent scripts.

Do not leave the project with ambiguous `long` and `short` filenames where their meaning is no longer clear.

Preserve the existing JSON schema where practical. Avoid unnecessary changes to downstream consumers.

## 3. Receipt PNG Generation

Generate two PNG images representing the weekly fixture reports.

Suggested filenames:

- `this-week.png`
- `next-week.png`

Use Python Pillow or an appropriate existing image-generation library.

### Appearance

The images should closely resemble the existing thermal printer output.

Requirements:

- Match the existing printed report's content, formatting and general proportions.
- Use a suitable monospace font.
- Use a warm off-white or slightly aged paper background.
- Render the fixture information clearly and legibly.
- Preserve existing fixture formatting, including dates, times and relevant competition/team information.
- Images should be generated from the weekly JSON datasets, not independently retrieved fixture data.

The physical printer output and digital receipt images should ideally share the same formatting logic. Refactor the existing output formatting into reusable functions if necessary, rather than maintaining two independent implementations.

The PNGs should be generated during the scheduled fixture generation process, not dynamically when someone visits the website.

## 4. Web Interface

Add a very simple single-page web interface to the existing project.

Do not introduce a separate container or service unless the existing architecture makes this unavoidable. Prefer extending the existing Python application.

### Visual direction

The aesthetic should resemble an old-school sports computing terminal.

**Background and typography:**
- Black or near-black background.
- Monospace typography throughout.
- Bright green or amber terminal-style text.
- ASCII art header, preferably incorporating a football/sports information network identity.
- Small supplementary terminal-style information, such as generation dates and system status.

**Main content:**

Display two receipt images:

- This Week
- Next Week

The receipts should:
- Sit side by side on desktop.
- Be displayed at their natural aspect ratio.
- Have a slight rotation, approximately -10 to +10 degrees.
- Have a subtle visual distinction from the black background.
- Look like physical pieces of thermal paper placed on a surface.

Use CSS transforms to achieve the rotation.

Rotation can be determined by the week number or another deterministic factor. Prefer this over genuinely random rotation on every page load, so the layout remains consistent throughout the week.

On smaller screens, stack the receipts vertically and ensure they remain readable without horizontal scrolling.

### Interface behaviour

Keep the interface deliberately minimal.

- No navigation.
- No conventional dashboard cards.
- No unnecessary buttons or controls.
- No client-side fixture fetching.
- No database requirement.
- No user accounts or authentication requirement unless already present in the application.

The web server should simply serve the latest generated receipt images and any supplementary metadata.

If images are missing, display a sensible fallback rather than producing a broken page.

## 5. Suggested Project Organisation

Adapt this to the existing project rather than restructuring everything unnecessarily.

An illustrative structure:

```text
football-fixtures/
├── app.py
├── fixtures.py
├── receipt_renderer.py
├── print.py
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── receipts/
│       ├── this-week.png
│       └── next-week.png
└── data/
    ├── full-range.json
    ├── this-week.json
    └── next-week.json
```

The existing project structure and naming conventions take precedence where appropriate.

## 6. Scheduling and Reliability

Preserve the existing Monday morning scheduled execution.

The generation workflow should:

1. Retrieve the ICS data.
2. Process and filter fixtures.
3. Write the full-range JSON.
4. Write both weekly JSON files.
5. Generate both receipt PNGs.
6. Print This Week's report through the existing print daemon.

Ensure that a failure in generating the website images does not silently result in incorrect or incomplete fixture data being printed.

Avoid unnecessary additional scheduled jobs. One weekly generation process should maintain all three datasets and both images.

## 7. Implementation and Testing

Before implementation:

- Inspect the existing scripts and identify how long and short JSON files are generated.
- Identify the current Monday scheduling mechanism.
- Identify how the thermal printer daemon is called.
- Understand the existing fixture JSON schema and printed formatting.

Test the following:

- This Week includes the correct Monday–Sunday range.
- Next Week includes the immediately following Monday–Sunday range.
- Fixtures on boundary dates are included correctly.
- The full-range JSON still covers the entire ICS date range.
- Both receipt images correspond to their respective JSON datasets.
- Only This Week is automatically printed.
- The web interface displays both images correctly.
- The interface works on desktop and mobile.
- Existing fixture filtering and printer functionality remain intact.

Provide a brief summary of files changed, any new dependencies, changes to scheduling and how to test the finished implementation.

Do not deploy changes or alter production scheduling without first ensuring the implementation is working correctly.