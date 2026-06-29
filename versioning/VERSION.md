Current Version: 12.11.0

V12.11.0 system change pack + Agent SOP + automatic recap

This release keeps the V12.10 task lifecycle and submit page split, then upgrades task quality:

- System layer extracts deterministic metric changes from uploaded reports and builds a systemChangePack.
- Agent layer reads the change pack, generates the operating judgment, executable SOP, task title and system recap line.
- Operator tasks no longer ask operators to split traffic sources, split ad plans, find ROI causes, or manually recap data.
- Operators only execute the Agent SOP and submit screenshots / notes / data evidence.
- After submission, later report uploads or interface refreshes trigger system auto-recap; recap results are written to daily reports, weekly reports and the recap library.
- When system recap misses the recap line, the system generates the next task automatically.
