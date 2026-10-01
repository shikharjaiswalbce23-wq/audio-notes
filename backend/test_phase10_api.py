
# test_phase10_api.py - FastAPI endpoint integration tests
import uuid
import io
import tempfile
import os
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from database import Base, get_db
import main


# -- DB + Client Fixtures -----------------------------------------------------

@pytest.fixture(scope='function')
def db_file(tmp_path):
    # Use a real temp file so all connections share the same DB
    db_path = str(tmp_path / 'test.db')
    return db_path


@pytest.fixture(scope='function')
def db_engine(db_file):
    engine = create_engine(
        f'sqlite:///{db_file}',
        connect_args={'check_same_thread': False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope='function')
def db(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope='function')
def client(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def _override_get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    main.app.dependency_overrides[get_db] = _override_get_db
    with TestClient(main.app, raise_server_exceptions=False) as c:
        yield c
    main.app.dependency_overrides.clear()


# -- helpers ------------------------------------------------------------------

def make_audio_file(filename='test.mp3', content_type='audio/mpeg'):
    return ('file', (filename, io.BytesIO(b'fake audio bytes'), content_type))


# -- GET /health --------------------------------------------------------------

def test_health_check_returns_ok(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json() == {'status': 'ok'}
    print('test_health_check_returns_ok PASSED')


# -- POST /uploads ------------------------------------------------------------

def test_upload_success_returns_201(client):
    with patch('main.storage_service.upload_file', return_value=True), \
         patch('main.q.enqueue'):
        resp = client.post('/uploads', files=[make_audio_file()])

    assert resp.status_code == 201
    body = resp.json()
    assert 'id' in body
    assert body['status'] == 'QUEUED'
    assert body['filename'] == 'test.mp3'
    assert body['progress'] == 0
    print('test_upload_success_returns_201 PASSED')


def test_upload_invalid_content_type_returns_400(client):
    resp = client.post(
        '/uploads',
        files=[('file', ('doc.pdf', io.BytesIO(b'pdf content'), 'application/pdf'))],
    )
    assert resp.status_code == 400
    assert 'Invalid file type' in resp.json()['detail']
    print('test_upload_invalid_content_type_returns_400 PASSED')


def test_upload_storage_failure_returns_500(client):
    with patch('main.storage_service.upload_file', return_value=False):
        resp = client.post('/uploads', files=[make_audio_file()])
    assert resp.status_code == 500
    assert 'Failed to upload' in resp.json()['detail']
    print('test_upload_storage_failure_returns_500 PASSED')


def test_upload_response_schema(client):
    with patch('main.storage_service.upload_file', return_value=True), \
         patch('main.q.enqueue'):
        resp = client.post('/uploads', files=[make_audio_file()])

    body = resp.json()
    for field in {'id', 'filename', 'status', 'progress', 'created_at', 'updated_at'}:
        assert field in body, f'Missing field: {field}'
    print('test_upload_response_schema PASSED')


def test_upload_enqueues_job(client):
    with patch('main.storage_service.upload_file', return_value=True), \
         patch('main.q.enqueue') as mock_enqueue:
        client.post('/uploads', files=[make_audio_file()])
    mock_enqueue.assert_called_once()
    print('test_upload_enqueues_job PASSED')


# -- GET /uploads/{upload_id} -------------------------------------------------

def test_get_upload_returns_record(client):
    with patch('main.storage_service.upload_file', return_value=True), \
         patch('main.q.enqueue'):
        post_resp = client.post('/uploads', files=[make_audio_file()])

    assert post_resp.status_code == 201, post_resp.text
    upload_id = post_resp.json()['id']
    get_resp = client.get(f'/uploads/{upload_id}')
    assert get_resp.status_code == 200
    assert get_resp.json()['id'] == upload_id
    print('test_get_upload_returns_record PASSED')


def test_get_upload_unknown_id_returns_404(client):
    resp = client.get(f'/uploads/{uuid.uuid4()}')
    assert resp.status_code == 404
    assert resp.json()['detail'] == 'Upload not found'
    print('test_get_upload_unknown_id_returns_404 PASSED')


def test_get_upload_invalid_uuid_returns_422(client):
    resp = client.get('/uploads/not-a-uuid')
    assert resp.status_code == 422
    print('test_get_upload_invalid_uuid_returns_422 PASSED')


def test_get_upload_reflects_completed_state(db_engine):
    # Write directly to DB, then verify endpoint reads it
    import crud, schemas
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def _override_get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    main.app.dependency_overrides[get_db] = _override_get_db
    session = Session()
    try:
        upload_in = schemas.UploadCreate(filename='direct.mp3', storage_key='key_direct.mp3')
        record = crud.create_upload(session, upload_in)
        crud.update_upload_status(session, record.id, status='COMPLETED', progress=100)
        crud.update_upload_results(session, record.id, transcript='Hi', summary='Summary.')
        session.commit()
        record_id = record.id
    finally:
        session.close()

    with TestClient(main.app, raise_server_exceptions=False) as c:
        resp = c.get(f'/uploads/{record_id}')

    main.app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body['status'] == 'COMPLETED'
    assert body['progress'] == 100
    assert body['transcript'] == 'Hi'
    assert body['summary'] == 'Summary.'
    print('test_get_upload_reflects_completed_state PASSED')


# -- Global exception handler -------------------------------------------------

def test_global_exception_handler_returns_json_500(client):
    with patch('main.crud.get_upload', side_effect=RuntimeError('Simulated DB crash')):
        resp = client.get(f'/uploads/{uuid.uuid4()}')

    assert resp.status_code == 500
    body = resp.json()
    assert 'detail' in body
    assert 'Simulated DB crash' not in body['detail']
    assert 'internal server error' in body['detail'].lower()
    print('test_global_exception_handler_returns_json_500 PASSED')
