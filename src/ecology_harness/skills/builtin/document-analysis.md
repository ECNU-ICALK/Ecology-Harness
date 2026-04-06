---
name: document-analysis
description: Analyze attached or workspace documents such as PDFs, DOCX files, notebooks, tables, and markdown notes.
slug: document-analysis
triggers: [/document-analysis]
allowed-tools: [DocumentInspect, DocumentExtract, Read, Glob, Grep]
context: inline
---
Analyze the requested document carefully.

Checklist:
- if the user attached a document to the current turn, reason over that attachment directly
- if the document lives in the workspace, use `DocumentInspect` first and `DocumentExtract` when more detail is needed
- identify document type, structure, and likely purpose before summarizing claims
- separate direct findings from your inferences
- if tables, methods, or headings matter, call them out explicitly

User context: $ARGUMENTS
