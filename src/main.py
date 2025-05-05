import os
import asyncio
from uuid import uuid4
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from core.config.pipeline_factory import pipeline_factory
from core.domain.progress_manager import progress_manager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://www.rafaelmarotta.dev", "http://www.rafaelmarotta.dev", "http://192.168.0.185"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretório onde os vídeos são salvos
VIDEO_DIR = os.getenv("OUTPUT_PATH", "")

# Models
class VideoRequest(BaseModel):
  pipeline: str
  text: str

class VideoResponse(BaseModel):
  text: str
  code: str

# Função que executa a pipeline em background
def run_pipeline_async(pipeline, context):
  pipeline.run(context)

# Endpoint para iniciar a geração de vídeo
@app.post("/videos", response_model=VideoResponse)
async def generate_video(req: VideoRequest):
  try:
    pipeline = pipeline_factory.create(req.pipeline)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))

  video_id = str(uuid4())

  context = {
    "id": video_id,
    "text": req.text,
    "number": "1",
  }

  loop = asyncio.get_event_loop()
  loop.run_in_executor(None, run_pipeline_async, pipeline, context)

  return VideoResponse(
    text="Your video is being generated",
    code=video_id
  )

# Endpoint para listar pipelines disponíveis
@app.get("/pipelines")
def list_pipelines():
  return pipeline_factory.list_pipelines()

# Endpoint de stream de progresso via SSE
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

          if message.startswith("video_ready"):
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

  return EventSourceResponse(
    event_generator(),
    headers=response_headers
  )


# Endpoint para retornar o vídeo final gerado
@app.get("/videos/file/{video_id}")
def get_video(video_id: str):
  path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")
  if not os.path.exists(path):
    raise HTTPException(status_code=404, detail="Video not found")
  return FileResponse(path, media_type="video/mp4")
