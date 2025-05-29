import os
import asyncio
import json
from uuid import uuid4
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from core.config.pipeline_factory import pipeline_factory
from core.domain.progress_manager import progress_manager
from core.domain.video_request_repository import VideoRequestRepository
from core.domain.video_metrics_repository import VideoMetricsRepository

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000", "https://www.rafaelmarotta.dev", "http://www.rafaelmarotta.dev", "http://192.168.0.185"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

video_request_repo = VideoRequestRepository()
video_metrics_repo = VideoMetricsRepository()


# Diretório onde os vídeos são salvos
VIDEO_DIR = os.getenv("OUTPUT_PATH", "")

# Models
class VideoRequest(BaseModel):
  pipeline: str
  text: str
  n: int
  tone_prompt: str

class VideoResponse(BaseModel):
  text: str
  code: str

# Cria o callback de progresso com suporte a event loop em thread separada
def make_callback(video_id: str, loop):
  def callback(message: str):
    async def handle():
      try:
        data = json.loads(message)
        event = data.get("event")

        if event == "video_ready":
          await video_request_repo.update_status(video_id, "completed")
        elif event == "export_progress":
          await video_request_repo.update_status(video_id, "processing")
      except Exception as e:
        print(f"Erro no callback do progresso do vídeo {video_id}: {e}")

    asyncio.run_coroutine_threadsafe(handle(), loop)

  return callback

# Função que executa a pipeline
def run_pipeline_async(pipeline, context, loop):
  progress_manager.subscribe(context["id"], make_callback(context["id"], loop))
  try:
    pipeline.run(context)
  except Exception as e:
    print(f"Erro ao executar a pipeline do vídeo {context['id']}: {e}")
    asyncio.run_coroutine_threadsafe(
      video_request_repo.update_status(context["id"], "failed"),
      loop
    )

# Endpoint para iniciar geração de vídeo
@app.post("/videos", response_model=VideoResponse)
async def generate_video(req: VideoRequest):
  try:
    pipeline = pipeline_factory.create(req.pipeline)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))

  video_id = str(uuid4())
  loop = asyncio.get_event_loop()

  context = {
    "id": video_id,
    "text": req.text,
    "n": req.n,
    "number": req.n,
    "tone_prompt": req.tone_prompt,
    "pipeline": req.pipeline,
    "loop": loop
  }

  await video_request_repo.create({
    "id": video_id,
    "pipeline": req.pipeline,
    "text": req.text,
    "n": req.n,
    "tone_prompt": req.tone_prompt,
    "status": "pending"
  })

  loop.run_in_executor(None, run_pipeline_async, pipeline, context, loop)

  return VideoResponse(
    text="Your video is being generated",
    code=video_id
  )

# Endpoint para listar pipelines disponíveis
@app.get("/pipelines")
def list_pipelines():
  return pipeline_factory.list_pipelines()

# SSE para progresso do vídeo
@app.get("/videos/stream/{video_id}")
async def video_progress_stream(video_id: str, request: Request):
  async def event_generator():
    queue = asyncio.Queue()

    def callback(message: str):
      queue.put_nowait(message)

    progress_manager.subscribe(video_id, callback)

    try:
      while True:
        if await request.is_disconnected():
          print(f"❌ Cliente desconectado do vídeo {video_id}")
          break

        try:
          message = await asyncio.wait_for(queue.get(), timeout=30)
          yield f"{message}"

          if '"event": "video_ready"' in message:
            await asyncio.sleep(0.5)
            break
        except asyncio.TimeoutError:
          yield "carregando ..."
    finally:
      progress_manager.unsubscribe(video_id, callback)

  origin = request.headers.get("origin")
  allowed_origins = {
    "http://localhost:3000",
    "https://www.rafaelmarotta.dev",
    "http://www.rafaelmarotta.dev",
    "http://192.168.0.185"
  }
  response_headers = {
    "Cache-Control": "no-cache",
    "Content-Type": "text/event-stream",
    "Connection": "keep-alive",
  }

  if origin in allowed_origins:
    response_headers["Access-Control-Allow-Origin"] = origin

  return EventSourceResponse(event_generator(), headers=response_headers)

# Endpoint para baixar vídeo
@app.get("/videos/file/{video_id}")
def get_video(video_id: str):
  path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")
  if not os.path.exists(path):
    raise HTTPException(status_code=404, detail="Video not found")
  return FileResponse(path, media_type="video/mp4")

# Endpoint para consultar uma requisição de vídeo
@app.get("/videos/{video_id}")
async def get_video_request(video_id: str):
  doc = await video_request_repo.get(video_id)
  if not doc:
    raise HTTPException(status_code=404, detail="Video request not found")
  doc.pop("_id", None)
  return JSONResponse(content=doc)

@app.get("/videos/metrics/{video_id}")
async def get_video_metrics(video_id: str):
  doc = await video_metrics_repo.get(video_id)
  if not doc:
    raise HTTPException(status_code=404, detail="Metrics not found")
  doc.pop("_id", None)
  return JSONResponse(content=doc)
