# -*-coding:utf8-*-
import json
import uuid
from bynamodb.exceptions import ItemNotFoundException
from flask import Blueprint, request, jsonify, abort
import time
from models import Note, Comment, DeletedArchive
from web.decorators import login_required
from web.utils import jsonable

bp = Blueprint('note', __name__)


@bp.route('/notes', methods=['GET'])
@login_required
def get_notes():
    def merge(l1, l2):
        i1, i2 = 0, 0
        result = []
        while i1 < len(l1) and i2 < len(l2):
            if l1[i1] < l2[i2]:
                result.append(l1[i1])
                i1 += 1
            else:
                result.append(l2[i2])
                i2 += 1
        return result + l1[i1:] + l2[i2:]

    if request.user.pair is None:
        return abort(400)

    u1, u2 = request.user.pair.user_ids
    u1_notes = Note.query(index_name='WriterIndex', writer_id=u1)
    u2_notes = Note.query(index_name='WriterIndex', writer_id=u2)
    return jsonify(notes=merge(u1_notes, u2_notes))


@bp.route('/', methods=['POST'])
@login_required
def write_note():
    required_params = 'title', 'content', 'is_secret'
    if any([param not in request.json for param in required_params]):
        return abort(400)

    note = Note.put_item(
        id=uuid.uuid1(),
        writer=request.user.id,
        published_at=time.time(),
        title=request.json['title'],
        content=request.json['content']
    )

    pair = request.user.pair
    pair.note_ids.append(note.id)
    pair.save()

    return jsonify(id=note.id), 201


@bp.route('/<path:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    try:
        note = Note.get_item(note_id)
    except ItemNotFoundException:
        return abort(404)

    if note.writer_id != request.user.id:
        return abort(403)

    DeletedArchive.put_item(
        type='NOTE',
        deleted_at=time.time(),
        owner_id=request.user.id,
        data=json.dumps(jsonable(note))
    )
    return '', 204


@bp.route('/<path:note_id>', methods=['GET'])
@login_required
def get_note(note_id):
    try:
        note = Note.get_item(note_id)
    except ItemNotFoundException:
        return abort(404)
    comments = Comment.query(note_id=note.id)
    return jsonify(note=jsonable(note), comments=jsonable(comments))


@bp.route('/<path:note_id>/comment', methods=['POST'])
@login_required
def write_comment(note_id):
    note = Note.get_item(note_id)
    if request.user.pair is None:
        return abort(400)
    if note.writer_id not in request.user.pair.user_ids:
        return abort(403)
    if 'content' not in request.json:
        return abort(400)
    content = request.json['content'].strip()
    if not content:
        return abort(400)

    comment = Comment.put_item(
        note_id=note.id,
        published_at=time.time(),
        writer_id=request.user.id,
        content=content
    )
    return jsonify(note_id=note_id, published_at=comment.published_at), 201
