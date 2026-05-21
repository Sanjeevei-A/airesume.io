"""
backend/routes/admin_routes.py
================================
Flask Blueprint: admin dashboard — view all analyses, stats, delete records.
"""

from flask import Blueprint, render_template, jsonify, request, abort
from backend.database import db, ResumeAnalysis

admin_bp = Blueprint('admin', __name__)

# NOTE: In production, protect all admin routes with authentication.
# For a fresher project, a simple session check is fine:
#   from flask import session
#   if not session.get('is_admin'): abort(401)


@admin_bp.route('/')
def dashboard():
    """Admin dashboard page."""
    return render_template('admin.html')


@admin_bp.route('/stats')
def stats():
    """Return aggregate statistics as JSON."""
    try:
        total   = ResumeAnalysis.query.count()
        records = ResumeAnalysis.query.all()
        scores  = [r.ats_score for r in records if r.ats_score is not None]

        grade_dist = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        for r in records:
            if r.ats_grade in grade_dist:
                grade_dist[r.ats_grade] += 1

        return jsonify({
            'total_resumes': total,
            'avg_score':     round(sum(scores) / len(scores), 1) if scores else 0,
            'max_score':     max(scores) if scores else 0,
            'min_score':     min(scores) if scores else 0,
            'grade_distribution': grade_dist,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/resumes')
def list_resumes():
    """Return paginated list of analyses."""
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    try:
        pagination = ResumeAnalysis.query.order_by(
            ResumeAnalysis.upload_time.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items':  [r.to_dict() for r in pagination.items],
            'total':  pagination.total,
            'pages':  pagination.pages,
            'page':   page,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/resumes/<int:analysis_id>', methods=['DELETE'])
def delete_resume(analysis_id: int):
    """Delete an analysis record."""
    record = ResumeAnalysis.query.get_or_404(analysis_id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'deleted': analysis_id}), 200
