from typing import List
from fastapi import APIRouter, HTTPException

from src.config_loader import load_works, save_works
from src.models import WorkConfig, TagConfig, CPConfig
from webui.backend.schemas.schemas import (
    WorkOut, WorkCreate, WorkRename,
    TagConfigOut, TagCreate, TagUpdate,
    CPConfigOut, CPCreate, ExcludeTagsUpdate,
)

router = APIRouter()


def _to_work_out(w: WorkConfig) -> WorkOut:
    return WorkOut(
        name=w.name,
        search_tags=w.search_tags,
        tags=[TagConfigOut(folder=t.folder, tags=t.tags, active=t.active) for t in w.tags],
        cp_tags=[CPConfigOut(members=cp.members, search_tags=cp.search_tags, name=cp.name) for cp in w.cp_tags],
        exclude_tags=w.exclude_tags,
        active=w.active,
    )


@router.get("/", response_model=List[WorkOut])
async def list_works():
    return [_to_work_out(w) for w in load_works()]


@router.post("/", response_model=WorkOut)
async def create_work(payload: WorkCreate):
    works = load_works()
    if any(w.name == payload.name for w in works):
        raise HTTPException(status_code=400, detail="作品已存在")
    works.append(WorkConfig(name=payload.name, search_tags=[], tags=[]))
    save_works(works)
    return _to_work_out(works[-1])


@router.put("/{name}", response_model=WorkOut)
async def rename_work(name: str, payload: WorkRename):
    works = load_works()
    for w in works:
        if w.name == name:
            w.name = payload.new_name
            save_works(works)
            return _to_work_out(w)
    raise HTTPException(status_code=404, detail="作品不存在")


@router.delete("/{name}")
async def delete_work(name: str):
    works = load_works()
    works = [w for w in works if w.name != name]
    save_works(works)
    return {"ok": True}


@router.patch("/{name}/toggle", response_model=WorkOut)
async def toggle_work(name: str):
    works = load_works()
    for w in works:
        if w.name == name:
            w.active = not w.active
            save_works(works)
            return _to_work_out(w)
    raise HTTPException(status_code=404, detail="作品不存在")


# ==================== Tags ====================

@router.get("/{name}/tags", response_model=List[TagConfigOut])
async def list_tags(name: str):
    works = load_works()
    for w in works:
        if w.name == name:
            return [TagConfigOut(folder=t.folder, tags=t.tags, active=t.active) for t in w.tags]
    raise HTTPException(status_code=404, detail="作品不存在")


@router.post("/{name}/tags", response_model=TagConfigOut)
async def add_tag(name: str, payload: TagCreate):
    works = load_works()
    for w in works:
        if w.name == name:
            if any(t.folder == payload.folder for t in w.tags):
                raise HTTPException(status_code=400, detail="角色已存在")
            tag = TagConfig(folder=payload.folder, tags=payload.tags)
            w.tags.append(tag)
            save_works(works)
            return TagConfigOut(folder=tag.folder, tags=tag.tags, active=tag.active)
    raise HTTPException(status_code=404, detail="作品不存在")


@router.put("/{name}/tags/{folder}", response_model=TagConfigOut)
async def update_tag(name: str, folder: str, payload: TagUpdate):
    works = load_works()
    for w in works:
        if w.name == name:
            for t in w.tags:
                if t.folder == folder:
                    if payload.tags is not None:
                        t.tags = payload.tags
                    if payload.active is not None:
                        t.active = payload.active
                    save_works(works)
                    return TagConfigOut(folder=t.folder, tags=t.tags, active=t.active)
            raise HTTPException(status_code=404, detail="角色不存在")
    raise HTTPException(status_code=404, detail="作品不存在")


@router.delete("/{name}/tags/{folder}")
async def delete_tag(name: str, folder: str):
    works = load_works()
    for w in works:
        if w.name == name:
            w.tags = [t for t in w.tags if t.folder != folder]
            save_works(works)
            return {"ok": True}
    raise HTTPException(status_code=404, detail="作品不存在")


# ==================== CP Tags ====================

@router.get("/{name}/cp-tags", response_model=List[CPConfigOut])
async def list_cp_tags(name: str):
    works = load_works()
    for w in works:
        if w.name == name:
            return [CPConfigOut(members=cp.members, search_tags=cp.search_tags, name=cp.name) for cp in w.cp_tags]
    raise HTTPException(status_code=404, detail="作品不存在")


@router.post("/{name}/cp-tags", response_model=CPConfigOut)
async def add_cp_tag(name: str, payload: CPCreate):
    works = load_works()
    for w in works:
        if w.name == name:
            cp = CPConfig(members=payload.members, search_tags=payload.search_tags)
            w.cp_tags.append(cp)
            save_works(works)
            return CPConfigOut(members=cp.members, search_tags=cp.search_tags, name=cp.name)
    raise HTTPException(status_code=404, detail="作品不存在")


@router.delete("/{name}/cp-tags/{index}")
async def delete_cp_tag(name: str, index: int):
    works = load_works()
    for w in works:
        if w.name == name:
            if 0 <= index < len(w.cp_tags):
                w.cp_tags.pop(index)
                save_works(works)
                return {"ok": True}
            raise HTTPException(status_code=404, detail="CP不存在")
    raise HTTPException(status_code=404, detail="作品不存在")


@router.put("/{name}/exclude-tags", response_model=WorkOut)
async def update_exclude_tags(name: str, payload: ExcludeTagsUpdate):
    works = load_works()
    for w in works:
        if w.name == name:
            w.exclude_tags = payload.tags
            save_works(works)
            return _to_work_out(w)
    raise HTTPException(status_code=404, detail="作品不存在")
