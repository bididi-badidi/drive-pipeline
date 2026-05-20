"""Local Gradio operator console for drive-pipeline."""

from __future__ import annotations

import gradio as gr

from pipeline import gradio_backend as backend

DRIVE_HEADERS = [
    "folder",
    "filename",
    "source_path",
    "extension",
    "size_bytes",
    "modified_at",
    "job_status",
]
GDRIVE_HEADERS = [
    "name",
    "folder",
    "size_bytes",
    "created_at",
    "modified_at",
    "web_view_link",
    "file_id",
]
VECTOR_HEADERS = [
    "chunk_id",
    "filename",
    "source_path",
    "source_type",
    "chunk_index",
    "total_chunks",
    "created_at",
    "distance",
    "preview",
]


def _rows(items: list[dict], headers: list[str]) -> list[list[object]]:
    return [[item.get(header, "") for header in headers] for item in items]


def refresh_drive() -> list[list[object]]:
    return _rows(backend.list_drive_files(), DRIVE_HEADERS)


def refresh_gdrive(limit: int) -> list[list[object]]:
    return _rows(backend.list_gdrive_archive(limit=int(limit)), GDRIVE_HEADERS)


def refresh_vectors(source_type: str, filename_contains: str, path_contains: str, limit: int):
    return _rows(
        backend.list_vector_items(
            source_type=source_type,
            filename_contains=filename_contains,
            source_path_contains=path_contains,
            limit=limit,
        ),
        VECTOR_HEADERS,
    )


def run_search(
    query_text: str,
    top_k: int,
    source_type: str,
    filename_contains: str,
    path_contains: str,
    raw_where_json: str,
):
    return _rows(
        backend.search_vector_items(
            query_text=query_text,
            top_k=top_k,
            source_type=source_type,
            filename_contains=filename_contains,
            source_path_contains=path_contains,
            raw_where_json=raw_where_json,
        ),
        VECTOR_HEADERS,
    )


def preview_delete(source_path: str):
    return backend.preview_delete(source_path).as_rows()


def confirm_delete(source_path: str, confirmed: bool):
    if not confirmed:
        return [["message", "Check confirm before deleting."]]
    return backend.delete_file_and_chunks(source_path, dry_run=False).as_rows()


def build_app() -> gr.Blocks:
    with gr.Blocks(title="drive-pipeline") as app:
        gr.Markdown("# drive-pipeline")
        source_types = ["", "document", "image", "url", "html"]

        with gr.Tab("Drive"):
            gr.Markdown("### Google Drive Archive")
            with gr.Row():
                gdrive_limit = gr.Number(value=200, precision=0, label="Limit")
            gdrive_table = gr.Dataframe(headers=GDRIVE_HEADERS, interactive=False)
            gr.Button("Refresh Drive").click(
                refresh_gdrive, inputs=gdrive_limit, outputs=gdrive_table
            )

            gr.Markdown("### Local Queue")
            drive_table = gr.Dataframe(headers=DRIVE_HEADERS, interactive=False)
            gr.Button("Refresh Local").click(refresh_drive, outputs=drive_table)

        with gr.Tab("Vector Store"):
            with gr.Row():
                vector_source_type = gr.Dropdown(source_types, value="", label="Source type")
                vector_filename = gr.Textbox(label="Filename contains")
                vector_path = gr.Textbox(label="Path contains")
                vector_limit = gr.Number(value=100, precision=0, label="Limit")
            vector_table = gr.Dataframe(headers=VECTOR_HEADERS, interactive=False)
            gr.Button("Refresh").click(
                refresh_vectors,
                inputs=[vector_source_type, vector_filename, vector_path, vector_limit],
                outputs=vector_table,
            )

        with gr.Tab("Search"):
            query_text = gr.Textbox(label="Query", lines=3)
            with gr.Row():
                top_k = gr.Number(value=10, precision=0, label="Top K")
                search_source_type = gr.Dropdown(source_types, value="", label="Source type")
                search_filename = gr.Textbox(label="Filename contains")
                search_path = gr.Textbox(label="Path contains")
            raw_where = gr.Textbox(label="Raw Chroma where JSON", lines=2)
            search_results = gr.Dataframe(headers=VECTOR_HEADERS, interactive=False)
            gr.Button("Search").click(
                run_search,
                inputs=[
                    query_text,
                    top_k,
                    search_source_type,
                    search_filename,
                    search_path,
                    raw_where,
                ],
                outputs=search_results,
            )

        with gr.Tab("Delete"):
            delete_path = gr.Textbox(label="Source path")
            delete_report = gr.Dataframe(headers=["field", "value"], interactive=False)
            gr.Button("Preview").click(preview_delete, inputs=delete_path, outputs=delete_report)
            confirm = gr.Checkbox(label="Confirm delete")
            gr.Button("Delete", variant="stop").click(
                confirm_delete,
                inputs=[delete_path, confirm],
                outputs=delete_report,
            )

    return app


def main() -> None:
    build_app().launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
