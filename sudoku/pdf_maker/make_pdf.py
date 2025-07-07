import json
import qrcode
import requests
import randfacts
from io import BytesIO
from datetime import datetime
from jinja2 import Environment, BaseLoader
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class SudokuPDFGenerator:
    def __init__(self, template_config=None):
        self.page_width, self.page_height = A4
        self.template_config = template_config or self.default_template_config()
        
    def default_template_config(self):
        return {
            'show_page_numbers': True,
            'show_qr_codes': True,
            'show_random_facts': True,
            'grid_size': 300,  # pixels
            'cell_size': 33,   # pixels per cell
            'margin_top': 72,
            'margin_bottom': 72,
            'margin_left': 72,
            'margin_right': 72,
            'title_font': 'Helvetica-Bold',
            'title_size': 24,
            'fact_font': 'Helvetica',
            'fact_size': 10
        }
    
    def generate_qr_code(self, puzzle_id, size=60):
        """Generate QR code for puzzle ID"""
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(f"Sudoku Puzzle: {puzzle_id}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    
    def get_random_fact(self):
        """Get a random fact for the page"""
        try:
            return randfacts.get_fact()
        except:
            return "Sudoku was invented in 1979 by Howard Garns, an American architect."
    
    def draw_sudoku_grid(self, canvas_obj, grid, x_start, y_start):
        """Draw the sudoku grid with numbers"""
        cell_size = self.template_config['cell_size']
        
        # Draw grid lines
        for i in range(10):
            line_width = 2 if i % 3 == 0 else 0.5
            canvas_obj.setLineWidth(line_width)
            
            # Vertical lines
            x = x_start + i * cell_size
            canvas_obj.line(x, y_start, x, y_start + 9 * cell_size)
            
            # Horizontal lines  
            y = y_start + i * cell_size
            canvas_obj.line(x_start, y, x_start + 9 * cell_size, y)
        
        # Fill in numbers
        canvas_obj.setFont("Helvetica", 16)
        for row in range(9):
            for col in range(9):
                if grid[row][col] != 0:
                    x = x_start + col * cell_size + cell_size/2
                    y = y_start + (8-row) * cell_size + cell_size/2 - 6
                    canvas_obj.drawCentredString(x, y, str(grid[row][col]))
    
    def create_page_template(self, canvas_obj, puzzle_id, puzzle_data, page_num):
        """Create a templated page with all elements"""
        config = self.template_config
        
        # Title
        canvas_obj.setFont(config['title_font'], config['title_size'])
        title_y = self.page_height - config['margin_top']
        canvas_obj.drawCentredString(self.page_width/2, title_y, f"Sudoku Puzzle - {puzzle_id}")
        
        # Difficulty badge
        canvas_obj.setFont("Helvetica", 12)
        difficulty = puzzle_data['d'].upper()
        canvas_obj.drawCentredString(self.page_width/2, title_y - 30, f"Difficulty: {difficulty}")
        
        # Sudoku grid
        grid_x = (self.page_width - config['grid_size']) / 2
        grid_y = self.page_height / 2 - config['grid_size'] / 2
        self.draw_sudoku_grid(canvas_obj, puzzle_data['q'], grid_x, grid_y)
        
        # QR Code (if enabled)
        if config['show_qr_codes']:
            qr_buffer = self.generate_qr_code(puzzle_id)
            qr_x = self.page_width - config['margin_right'] - 60
            qr_y = self.page_height - config['margin_top'] - 60
            canvas_obj.drawImage(qr_buffer, qr_x, qr_y, width=60, height=60)
        
        # Random fact (if enabled)
        if config['show_random_facts']:
            fact = self.get_random_fact()
            canvas_obj.setFont(config['fact_font'], config['fact_size'])
            fact_y = config['margin_bottom'] + 30
            # Text wrapping for long facts
            words = fact.split(' ')
            lines = []
            current_line = ""
            max_width = self.page_width - 2 * config['margin_left']
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if canvas_obj.stringWidth(test_line, config['fact_font'], config['fact_size']) < max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            for i, line in enumerate(lines):
                canvas_obj.drawString(config['margin_left'], fact_y - i * 12, line)
        
        # Page number (if enabled)
        if config['show_page_numbers']:
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.drawCentredString(self.page_width/2, config['margin_bottom'], f"Page {page_num}")
    
    def generate_pdf(self, sudoku_json_file, output_file):
        """Generate the complete PDF book"""
        # Load sudoku data
        with open(sudoku_json_file, 'r') as f:
            sudoku_data = json.load(f)
        
        # Create PDF
        canvas_obj = canvas.Canvas(output_file, pagesize=A4)
        
        page_num = 1
        for puzzle_id, puzzle_data in sudoku_data.items():
            self.create_page_template(canvas_obj, puzzle_id, puzzle_data, page_num)
            canvas_obj.showPage()
            page_num += 1
        
        canvas_obj.save()
        print(f"PDF generated: {output_file}")

# Usage example
if __name__ == "__main__":
    # Custom template configuration
    custom_config = {
        'show_page_numbers': True,
        'show_qr_codes': False,
        'show_random_facts': True,
        'grid_size': 280,
        'cell_size': 31,
        'margin_top': 80,
        'margin_bottom': 60,
        'margin_left': 60,
        'margin_right': 60,
        'title_font': 'Helvetica-Bold',
        'title_size': 20,
        'fact_font': 'Helvetica',
        'fact_size': 9
    }
    
    generator = SudokuPDFGenerator(custom_config)
    generator.generate_pdf('sudoku.json', 'sudoku_book.pdf')
