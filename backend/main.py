from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from estimator_service import process_estimation


app = FastAPI(title="Stimation Tool API")


# In production, restrict origins to the SharePoint tenant/site only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tenant.sharepoint.com",
    ],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.post("/api/stimation/estimate")
async def estimate(
    mode: str = Form(...),
    includeAudit: str = Form("false"),
    file: UploadFile = File(...),
):
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    if mode not in ("ofertas", "equipos"):
        raise HTTPException(status_code=400, detail="mode must be 'ofertas' or 'equipos'.")

    include_audit = str(includeAudit).lower() == "true"

    try:
        input_bytes = await file.read()

        output_bytes, output_name = process_estimation(
            input_bytes=input_bytes,
            original_filename=file.filename,
            mode=mode,
            include_audit=include_audit,
        )

        return Response(
            content=output_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={output_name}"
            },
        )

    except FileNotFoundError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
