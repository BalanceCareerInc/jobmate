# -*-coding:utf8-*-
from os import abort
import uuid
from flask import Blueprint, request, jsonify
import time
from models import Note, Pair
from web.decorators import login_required

bp = Blueprint('note', __name__)


@bp.route('/write', methods=['POST'])
@login_required
def write():
    required_params = 'title', 'content', 'is_secret'
    [abort(400) for param in required_params if param not in request.json]

    note = Note.put_item(
        id=uuid.uuid1(),
        writer=request.user.id,
        published_at=time.time(),
        title=request.json['title'],
        content=request.json['content']
    )

    request.pair.note_ids.append(note.id)
    request.pair.save()

    return jsonify(id=note.id)
