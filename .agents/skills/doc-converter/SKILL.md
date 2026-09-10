---
name: doc-converter
description: >
  Document conversion, chunking, and semantic indexing skill for PDFs, Excel (.xlsx), and Word (.docx) files.
  Provides AI agents with instructions and tools to translate documents into Markdown and query them in CaveMem.
  Triggers when handling .pdf, .xlsx, .docx files, or when converting documents.
version: 1.0.0
---

# doc-converter — Document Conversion & Semantic Retrieval Skill

This skill provides AI agents with the tools and guidelines to parse, extract, and semantically index external document files (PDF, Word, Excel) to incorporate clean code paradigms and project documentation directly into development workflows.

---

## CONVERSION UTILITIES

When encountering document files, you can convert them directly to formatted Markdown using the following built-in scripts:

### 1. PDF Documents (`.pdf`)
Convert raw PDF text page-by-page to structured Markdown:
```bash
rtk python scripts/pdf_to_markdown.py input.pdf -o output.md
```
*Options:*
- `--start-page N`: Start extracting from page N (1-indexed).
- `--end-page M`: Stop extracting at page M (inclusive, 1-indexed).

### 2. Excel Spreadsheets (`.xlsx`)
Convert spreadsheets into clean Markdown tables:
```bash
rtk python scripts/excel_to_markdown.py input.xlsx -o output.md
```
*Options:*
- `-s Sheet1 Sheet2`: Limit extraction to specific sheets (space separated).

### 3. Word Documents (`.docx`)
Convert text paragraphs, headers, bullet lists, and tables to Markdown:
```bash
rtk python scripts/docx_to_markdown.py input.docx -o output.md
```

---

## CAVEMEM INDEXING & SEMANTIC RETRIEVAL

To absorb entire textbooks or technical reference docs into the project's permanent knowledge base:

### 1. Indexing Chunks
Partition any Markdown/Text document and upload it to CaveMem under the custom `docs` category:
```bash
rtk python scripts/doc_to_cavemem.py output.md --project <project_name>
```
*Options:*
- `--chunk-size N`: Custom chunk size (default: 1200 characters).
- `--overlap M`: Custom chunk overlap size (default: 200 characters).
- `--category <name>`: Custom category (defaults to `docs`).

### 2. Semantic Querying
Retrieve technical rules or textbook recommendations semantically:
```bash
rtk cavemem query "<technical query or refactoring pattern>"
```
This enables real-time context enhancement by drawing from the parsed documentation database.
