# Generated Workflow Instances

This directory is reserved for generated WfCommons workflow instances.

The default generator output is:

```text
data/wfcommons/{workflow_type}/{requested_size}/{workflow_type}_{requested_size}_{instance_id}.json
```

Generated JSON files are ignored by Git by default because they can become large. Regenerate them locally with:

```powershell
.\.venv\Scripts\python.exe scripts\generate_wfcommons_instances.py
```
