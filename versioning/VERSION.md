Current Version: 16.17

V16.17 legacy ImportJob route removal.

Data import uses src/api/routes/data_import.py only. The old ImportJob wrapper route and worker services were removed from active runtime.

Verify with scripts/check_v16_manifest.py
