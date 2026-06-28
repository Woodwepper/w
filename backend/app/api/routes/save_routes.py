from app.persistence import save_repository
from app.persistence.save_models import GameSave
from fastapi import APIRouter, HTTPException
from app.api import memory_store

router = APIRouter(prefix="/api", tags=["Factory Lab API V2"])

def _create_world_save(world_id: int, name: str, save_type: str):
    world = memory_store.get_world_or_404(world_id)
    save = save_repository.create_save(
        GameSave(
            id=None,
            world_id=world.id,
            name=name,
            save_type=save_type,
            world_data_json=world.to_dict(),
        )
    )
    return {
        "message": "World saved successfully.",
        "save_id": save.id,
        "world_id": save.world_id,
        "name": save.name,
        "save_type": save.save_type,
        "created_at": save.created_at,
        "updated_at": save.updated_at,
    }

@router.post("/worlds/{world_id}/manualsave")
def manual_save(world_id: int, name: str):
    return _create_world_save(world_id, name, "manual")

@router.post("/worlds/{world_id}/quicksave")
def quick_save(world_id: int):
    return _create_world_save(world_id, "Quick Save", "quicksave")

@router.post("/worlds/{world_id}/autosave")
def auto_save(world_id: int):
    return _create_world_save(world_id, "Auto Save", "autosave")

@router.get("/worlds/{world_id}/saves")
def list_saves(world_id: int):
    world_saves = save_repository.list_saves_by_world_id(world_id)
    
    return {
        "saves": [
            {
                "id": save.id,
                "world_id": save.world_id,
                "name": save.name,
                "save_type": save.save_type,
                "created_at": save.created_at,
                "updated_at": save.updated_at,
            }
            for save in world_saves
        ]
    }

@router.patch("/worlds/{world_id}/saves/{save_id}")
def update_save(world_id: int, save_id: int, name: str):
    world = memory_store.get_world_or_404(world_id)
    save = save_repository.get_save(save_id)
    if save is None or save.world_id != world.id:
        raise HTTPException(status_code=404, detail="Save not found for this world")

    updated_save = save_repository.update_save(
        GameSave(
            id=save.id,
            world_id=save.world_id,
            name=name,
            save_type=save.save_type,
            world_data_json=world.to_dict(),
            created_at=save.created_at,
            updated_at=save.updated_at,
        )
    )
    if updated_save is None:
        raise HTTPException(status_code=500, detail="Failed to update save")

    return {
        "message": "Save updated successfully.",
        "save_id": updated_save.id,
        "world_id": updated_save.world_id,
        "name": updated_save.name,
        "save_type": updated_save.save_type,
        "created_at": updated_save.created_at,
        "updated_at": updated_save.updated_at,
    }

@router.delete("/worlds/{world_id}/saves/{save_id}")
def delete_save(world_id: int, save_id: int):
    save = save_repository.get_save(save_id)

    if save is None or save.world_id != world_id:
        raise HTTPException(
            status_code=404,
            detail="Save not found for this world",
        )

    success = save_repository.delete_save(save_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete save",
        )

    return {
        "message": "Save deleted successfully.",
        "save_id": save.id,
        "world_id": save.world_id,
        "name": save.name,
        "save_type": save.save_type,
        "created_at": save.created_at,
        "updated_at": save.updated_at,
    }

@router.post("/worlds/saves/{save_id}/load")
def load_save(save_id: int):
    world = save_repository.load_world(save_id)
    
    if world is None:
        raise HTTPException(status_code=404, detail="Save not found")
    
    memory_store.replace_world(world)
    
    return {
        "message": "Save loaded successfully",
        "world_id": world.id,
        "save_id": save_id
    }