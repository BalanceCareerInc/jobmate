# -*-coding:utf8-*-
import uuid
from flask import Blueprint, request, jsonify, abort
import time
from models import Note, Comment
from web.decorators import login_required
from web.utils import jsonable

bp = Blueprint('note', __name__)


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

    return jsonify(id=note.id)


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

    if request.user.pair_id is None:
        return abort(400)

    u1, u2 = request.user.pair.user_ids
    u1_notes = Note.query(index_name='WriterIndex', writer_id=u1)
    u2_notes = Note.query(index_name='WriterIndex', writer_id=u2)
    return jsonify(notes=merge(u1_notes, u2_notes))





@bp.route('/<path:note_id>', methods=['GET'])
@login_required
def get_note(note_id):
    note = Note.get_item(note_id)
    comments = Comment.query(note_id=note.id)
    return jsonify(note=jsonable(note), comments=jsonable(comments))
