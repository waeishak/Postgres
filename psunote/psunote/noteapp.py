import flask
import models
import forms

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


def get_or_create_tag(db, tag_name):
    """Return existing tag or create a new one."""
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
    ).scalars().first()
    if not tag:
        tag = models.Tag(name=tag_name)
        db.session.add(tag)
    return tag


def assign_tags_to_note(db, note, tag_names):
    """Assign tags to a note."""
    note.tags.clear()
    for tag_name in tag_names:
        tag = get_or_create_tag(db, tag_name)
        note.tags.append(tag)


def remove_orphan_tags(db):
    """Delete tags that are no longer associated with any notes."""
    orphan_tags = db.session.execute(
        db.select(models.Tag).where(~models.Tag.notes.any())
    ).scalars().all()
    for tag in orphan_tags:
        db.session.delete(tag)
    db.session.commit()


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template("index.html", notes=notes)


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    db = models.db

    if form.validate_on_submit():
        note = models.Note(title=form.title.data, description=form.description.data)
        assign_tags_to_note(db, note, form.tags.data)
        db.session.add(note)
        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("notes-create.html", form=form, title="Create Note")


@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalar_one_or_none()

    if not note:
        flask.abort(404)

    form = forms.NoteForm(obj=note)

    if form.validate_on_submit():
        note.title = form.title.data
        note.description = form.description.data
        assign_tags_to_note(db, note, form.tags.data)
        db.session.commit()
        remove_orphan_tags(db)
        return flask.redirect(flask.url_for("index"))

    return flask.render_template(
        "notes-create.html",
        form=form,
        note=note,
        title=f"Edit Note: {note.title}"
    )


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def notes_delete(note_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalar_one_or_none()

    if note:
        db.session.delete(note)
        db.session.commit()
        remove_orphan_tags(db)

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
    ).scalars().first()

    notes = []
    if tag:
        notes = db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag.id))
        ).scalars()

    return flask.render_template("tags-view.html", tag_name=tag_name, notes=notes)


if __name__ == "__main__":
    app.run(debug=True)
