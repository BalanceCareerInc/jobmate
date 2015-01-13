# -*-coding:utf8-*-
from os import abort
import uuid
from flask import Blueprint, request, jsonify
import time
from models import Note
from web.decorators import login_required

bp = Blueprint('note', __name__)


@bp.route('/write', methods=['POST'])
@login_required
def write():
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

    request.pair.note_ids.append(note.id)
    request.pair.save()

    return jsonify(id=note.id)
