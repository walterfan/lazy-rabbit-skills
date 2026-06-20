# Diagram Render — Detailed Guide

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `type` | Diagram type: `plantuml`, `mermaid`, `graphviz`, or `dot` |
| `-i, --input` | Input file (reads from stdin if not specified) |
| `-o, --output` | Output file path |
| `-f, --format` | Output format: `png` (default) or `svg` |
| `--base64` | Output base64-encoded image to stdout |
| `-v, --verbose` | Show progress messages |

## Supported Diagram Types

| Type | Code Block | File Extension | Description |
|------|------------|----------------|-------------|
| PlantUML | \`\`\`plantuml | `.puml` | UML diagrams, mind maps, sequence diagrams, class diagrams |
| Mermaid | \`\`\`mermaid | `.mmd` | Flowcharts, sequence diagrams, ER diagrams, Gantt charts |
| Graphviz | \`\`\`dot or \`\`\`graphviz | `.dot` | Directed/undirected graphs, network diagrams |

## Rendering Methods

### PlantUML
- Uses the public PlantUML server (https://www.plantuml.com/plantuml)
- Encodes diagram using PlantUML's custom compression format
- Configurable via `PLANTUML_SERVER` environment variable

### Graphviz
1. Tries python-graphviz library first
2. Falls back to `dot` binary if library unavailable

### Mermaid
1. Uses `mmdc` (mermaid-cli) if installed
2. Falls back to `npx @mermaid-js/mermaid-cli` if npx available

## Batch Processing Markdown Files

When processing a markdown file that contains diagram code blocks:

1. **Scan** for fenced code blocks tagged `plantuml`, `mermaid`, `dot`, or `graphviz`
2. **Extract** each block's source to a temp file
3. **Generate a descriptive filename** based on diagram content (e.g., `auth_sequence.png`)
4. **Render** using the script:
   ```bash
   python scripts/render_diagram.py <type> \
       -i /tmp/diagram.<ext> \
       -o images/<descriptive_name>.png
   ```
5. **Insert an image reference** below the code block:
   ```markdown
   ![Description](images/<descriptive_name>.png)
   ```
6. **Keep the source code block** — it enables future re-rendering

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PLANTUML_SERVER` | `https://www.plantuml.com/plantuml` | PlantUML server URL |

## Error Handling

| Error | Fix |
|-------|-----|
| `requests package required` | `pip install requests` |
| `Graphviz not available` | `brew install graphviz` (macOS) / `apt install graphviz` (Ubuntu) / `pip install graphviz` |
| `mermaid-cli (mmdc) not found` | `npm install -g @mermaid-js/mermaid-cli` |
| `SSL verification failed` | Update CA certs or set `PLANTUML_SERVER` to a local server |
| `dot failed` / `mmdc failed` | Syntax error in diagram source — check error message |
| Script not found | Run from workspace root: `python scripts/render_diagram.py --help` |
| Permission denied | `chmod +x scripts/render_diagram.py` |
| PlantUML server unreachable | `docker run -d -p 8080:8080 plantuml/plantuml-server:jetty` then `export PLANTUML_SERVER=http://localhost:8080` |

## Tips

- **Always keep source code blocks** — enables future re-rendering
- **Use meaningful filenames** — `auth_sequence.png` over `diagram1.png`
- **Prefer PNG** for complex diagrams with many elements
- **Prefer SVG** for docs viewed at different sizes
