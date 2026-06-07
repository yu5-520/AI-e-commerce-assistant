from pathlib import Path
import sys
out=sys.argv[1] if len(sys.argv)>1 else 'analysis-result.md'
Path(out).write_text('# PDD Analysis\n\nOK: action ran successfully.\n',encoding='utf-8')
