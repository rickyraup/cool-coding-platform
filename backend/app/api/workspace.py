"""Workspace item management API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from app.models.postgres_models import WorkspaceItem, CodeSession
from app.schemas.postgres_schemas import (
    WorkspaceItemCreate,
    WorkspaceItemUpdate,
    WorkspaceItemResponse,
    WorkspaceItemListResponse,
    WorkspaceItemDetailResponse,
    WorkspaceTreeResponse,
    BaseResponse
)
from app.api.postgres_sessions import (
    convert_workspace_item_to_response,
    build_workspace_tree
)

router = APIRouter()

@router.post("/", response_model=WorkspaceItemDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace_item(item_data: WorkspaceItemCreate):
    """Create a new workspace item (file or folder)."""
    try:
        # Verify session exists
        session = CodeSession.get_by_id(item_data.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify parent exists if parent_id is provided
        if item_data.parent_id:
            parent = WorkspaceItem.get_by_id(item_data.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent item not found"
                )
            if parent.type != 'folder':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent must be a folder"
                )
        
        # Create workspace item
        new_item = WorkspaceItem.create(
            session_id=item_data.session_id,
            name=item_data.name,
            item_type=item_data.type,
            parent_id=item_data.parent_id,
            content=item_data.content
        )
        
        item_response = convert_workspace_item_to_response(new_item)
        
        return WorkspaceItemDetailResponse(
            success=True,
            message="Workspace item created successfully",
            data=item_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workspace item: {str(e)}"
        )

@router.get("/{item_id}", response_model=WorkspaceItemDetailResponse)
async def get_workspace_item(item_id: int):
    """Get a specific workspace item."""
    try:
        item = WorkspaceItem.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace item not found"
            )
        
        item_response = convert_workspace_item_to_response(item)
        
        return WorkspaceItemDetailResponse(
            success=True,
            message="Workspace item retrieved successfully",
            data=item_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workspace item: {str(e)}"
        )

@router.put("/{item_id}", response_model=WorkspaceItemDetailResponse)
async def update_workspace_item(item_id: int, item_update: WorkspaceItemUpdate):
    """Update a workspace item."""
    try:
        item = WorkspaceItem.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace item not found"
            )
        
        # Update name if provided
        if item_update.name is not None:
            success = item.rename(item_update.name)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update item name"
                )
        
        # Update content if provided (only for files)
        if item_update.content is not None:
            if item.type != 'file':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Content can only be updated for files"
                )
            success = item.update_content(item_update.content)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update item content"
                )
        
        # Get updated item
        updated_item = WorkspaceItem.get_by_id(item_id)
        item_response = convert_workspace_item_to_response(updated_item)
        
        return WorkspaceItemDetailResponse(
            success=True,
            message="Workspace item updated successfully",
            data=item_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workspace item: {str(e)}"
        )

@router.delete("/{item_id}", response_model=BaseResponse)
async def delete_workspace_item(item_id: int):
    """Delete a workspace item and all its children."""
    try:
        item = WorkspaceItem.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace item not found"
            )
        
        success = item.delete()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete workspace item"
            )
        
        return BaseResponse(
            success=True,
            message="Workspace item deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workspace item: {str(e)}"
        )

@router.get("/session/{session_id}/tree", response_model=WorkspaceTreeResponse)
async def get_session_workspace_tree(session_id: int):
    """Get the workspace tree structure for a session."""
    try:
        # Verify session exists
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get all workspace items for this session
        workspace_items = WorkspaceItem.get_all_by_session(session_id)
        workspace_tree = build_workspace_tree(workspace_items)
        
        return WorkspaceTreeResponse(
            success=True,
            message="Workspace tree retrieved successfully",
            data=workspace_tree
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workspace tree: {str(e)}"
        )

@router.get("/session/{session_id}", response_model=WorkspaceItemListResponse)
async def get_session_workspace_items(
    session_id: int,
    parent_id: Optional[int] = None
):
    """Get workspace items for a session, optionally filtered by parent."""
    try:
        # Verify session exists
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if parent_id is not None:
            # Get items for specific parent
            items = WorkspaceItem.get_by_session_and_parent(session_id, parent_id)
        else:
            # Get all items for session
            items = WorkspaceItem.get_all_by_session(session_id)
        
        item_responses = [convert_workspace_item_to_response(item) for item in items]
        
        return WorkspaceItemListResponse(
            success=True,
            message=f"Retrieved {len(item_responses)} workspace items",
            data=item_responses,
            count=len(item_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workspace items: {str(e)}"
        )