from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import json
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch

reports_bp = Blueprint('reports', __name__)

# Path to store reports data
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'data')
REPORTS_FILE = os.path.join(REPORTS_DIR, 'reports.json')

# Ensure directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

def load_reports():
    """Load reports from JSON file"""
    if os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_reports(reports):
    """Save reports to JSON file"""
    with open(REPORTS_FILE, 'w') as f:
        json.dump(reports, f, indent=2)

@reports_bp.route('/', methods=['GET'])
def get_reports():
    """Get all generated reports"""
    try:
        reports = load_reports()
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a new report from scan history"""
    try:
        data = request.json
        scans = data.get('scans', [])
        report_name = data.get('name', f"Security Scan Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        reports = load_reports()
        
        # Create new report
        new_report = {
            'id': f"report_{len(reports) + 1}_{int(datetime.now().timestamp())}",
            'name': report_name,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'scans': scans,
            'total_scans': len(scans),
            'created_at': datetime.now().isoformat()
        }
        
        reports.insert(0, new_report)
        save_reports(reports)
        
        return jsonify({'success': True, 'report': new_report}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/delete/<report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Delete a report"""
    try:
        reports = load_reports()
        reports = [r for r in reports if r['id'] != report_id]
        save_reports(reports)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/export/<report_id>', methods=['GET'])
def export_report(report_id):
    """Export report as PDF"""
    try:
        reports = load_reports()
        report = next((r for r in reports if r['id'] == report_id), None)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0ea5e9'),
            spaceAfter=30,
            alignment=1  # Center
        )
        elements.append(Paragraph(report['name'], title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Report Info
        info_data = [
            ['Report Generated:', report['date']],
            ['Total Scans:', str(report['total_scans'])],
            ['Report ID:', report['id']]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Scan History
        elements.append(Paragraph('Scan History', styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        if report['scans']:
            scan_data = [['Tool', 'Date/Time']]
            for scan in report['scans']:
                scan_data.append([scan.get('tool', 'N/A'), scan.get('date', 'N/A')])
            
            scan_table = Table(scan_data, colWidths=[3*inch, 3*inch])
            scan_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(scan_table)
        else:
            elements.append(Paragraph('No scans recorded in this report.', styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{report['name'].replace(' ', '_')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500