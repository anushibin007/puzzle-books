import json
import qrcode
import requests
import randfacts
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


class SudokuPDFGeneratorA5:
    def __init__(self, template_config=None):
        self.page_width, self.page_height = A5  # 420 x 595 points
        self.template_config = template_config or self.default_template_config()
        
    def default_template_config(self):
        """Optimized configuration for A5 size with centered layout"""
        return {
            'show_page_numbers': True,
            'show_qr_codes': True,
            'show_random_facts': True,
            'grid_size': 360,      # Optimized for A5
            'cell_size': 40,       # 360/9 = 40 points per cell
            'margin': 30,          # Smaller margins for A5
            'title_font': 'Helvetica-Bold',
            'title_size': 18,      # Slightly smaller for A5
            'difficulty_font': 'Helvetica',
            'difficulty_size': 12,
            'fact_font': 'Helvetica',
            'fact_size': 8,        # Smaller fact text for A5
            'page_number_font': 'Helvetica',
            'page_number_size': 9,
            'qr_size': 45          # Smaller QR code for A5
        }
    
    def generate_qr_code(self, puzzle_id):
        """Generate QR code for puzzle ID pointing to your site URL."""
        url = (
            "https://book.fastorial.dev/puzzle-books"
            "?category=sudoku"
            "&volume=1"
            f"&puzzle={puzzle_id}"
        )
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(url)
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
            return "Sudoku helps improve memory, concentration, and logical thinking skills."
    
    def get_centered_positions(self):
        """Calculate centered positions for all elements"""
        config = self.template_config
        
        # Grid centered both horizontally and vertically
        grid_x = (self.page_width - config['grid_size']) / 2
        grid_y = (self.page_height - config['grid_size']) / 2
        
        # Other elements positioned relative to centered grid
        positions = {
            'grid_x': grid_x,
            'grid_y': grid_y,
            'title_x': self.page_width / 2,
            'title_y': grid_y + config['grid_size'] + 40,
            'difficulty_x': self.page_width / 2,
            'difficulty_y': grid_y + config['grid_size'] + 15,
            'page_number_x': self.page_width / 2,
            'page_number_y': grid_y - 30,
            'fact_x': config['margin'],
            'fact_y': grid_y - 50,
            'qr_x': self.page_width - config['margin'] - config['qr_size'],
            'qr_y': grid_y + config['grid_size'] - config['qr_size']
        }
        
        return positions
    
    def draw_sudoku_grid(self, canvas_obj, grid, x_start, y_start):
        """Draw the sudoku grid with numbers - optimized for A5"""
        cell_size = self.template_config['cell_size']
        
        # Draw grid lines with appropriate thickness
        for i in range(10):
            line_width = 1.5 if i % 3 == 0 else 0.5
            canvas_obj.setLineWidth(line_width)
            
            # Vertical lines
            x = x_start + i * cell_size
            canvas_obj.line(x, y_start, x, y_start + 9 * cell_size)
            
            # Horizontal lines  
            y = y_start + i * cell_size
            canvas_obj.line(x_start, y, x_start + 9 * cell_size, y)
        
        # Fill in numbers with appropriate font size for A5
        canvas_obj.setFont("Helvetica", 14)  # Slightly smaller font for A5
        canvas_obj.setFillColor(colors.black)
        
        for row in range(9):
            for col in range(9):
                if grid[row][col] != 0:  # Changed from 'x' to 0
                    x = x_start + col * cell_size + cell_size/2
                    y = y_start + (8-row) * cell_size + cell_size/2 - 5
                    canvas_obj.drawCentredString(x, y, str(grid[row][col]))
    
    def wrap_text(self, canvas_obj, text, max_width, font_name, font_size):
        """Wrap text to fit within specified width"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if canvas_obj.stringWidth(test_line, font_name, font_size) < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def create_centered_page(self, canvas_obj, puzzle_id, puzzle_data, page_num):
        """Create a fully centered page layout for A5"""
        config = self.template_config
        pos = self.get_centered_positions()
        
        # Title - centered at top
        canvas_obj.setFont(config['title_font'], config['title_size'])
        canvas_obj.setFillColor(colors.black)
        canvas_obj.drawCentredString(pos['title_x'], pos['title_y'], 
                                  f"Sudoku Puzzle")
        
        # Puzzle ID - centered below title
        canvas_obj.setFont(config['difficulty_font'], config['difficulty_size'])
        canvas_obj.drawCentredString(pos['difficulty_x'], pos['difficulty_y'] + 10, 
                                  puzzle_id)
        
        # Difficulty badge - centered
        difficulty = puzzle_data['d'].upper()  # Changed from 'difficulty' to 'd'
        
        # Create colored difficulty indicator
        difficulty_colors = {
            'EASY': colors.green,
            'MEDIUM': colors.orange, 
            'HARD': colors.red
        }
        
        badge_color = difficulty_colors.get(difficulty, colors.gray)
        badge_width = 60
        badge_height = 15
        badge_x = pos['difficulty_x'] - badge_width/2
        badge_y = pos['difficulty_y'] - 5
        
        canvas_obj.setFillColor(badge_color)
        canvas_obj.rect(badge_x, badge_y, badge_width, badge_height, fill=1)
        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawCentredString(pos['difficulty_x'], badge_y + 4, difficulty)
        
        # Sudoku grid - perfectly centered
        canvas_obj.setFillColor(colors.black)
        self.draw_sudoku_grid(canvas_obj, puzzle_data['q'], pos['grid_x'], pos['grid_y'])  # Changed from 'question' to 'q'
        
        # QR Code – wrap BytesIO in ImageReader
        if config['show_qr_codes']:
            qr_buffer = self.generate_qr_code(puzzle_id)  # returns BytesIO
            qr_img = ImageReader(qr_buffer)               # wrap for ReportLab
            canvas_obj.drawImage(
                qr_img,
                pos['qr_x'],
                pos['qr_y'],
                width=config['qr_size'],
                height=config['qr_size'],
                preserveAspectRatio=True,
                mask='auto'
            )
        
        # Random fact - bottom area, centered (if enabled)
        if config['show_random_facts']:
            fact = self.get_random_fact()
            canvas_obj.setFont(config['fact_font'], config['fact_size'])
            canvas_obj.setFillColor(colors.darkgray)
            
            # Wrap text for A5 width
            max_fact_width = self.page_width - 2 * config['margin']
            fact_lines = self.wrap_text(canvas_obj, fact, max_fact_width, 
                                      config['fact_font'], config['fact_size'])
            
            # Center the fact text block
            for i, line in enumerate(fact_lines):
                line_width = canvas_obj.stringWidth(line, config['fact_font'], config['fact_size'])
                line_x = (self.page_width - line_width) / 2
                canvas_obj.drawString(line_x, pos['fact_y'] - i * 10, line)
        
        # Page number - centered at bottom (if enabled)
        if config['show_page_numbers']:
            canvas_obj.setFont(config['page_number_font'], config['page_number_size'])
            canvas_obj.setFillColor(colors.black)
            canvas_obj.drawCentredString(pos['page_number_x'], pos['page_number_y'], 
                                     f"— {page_num} —")
    
    def generate_pdf(self, sudoku_json_file, output_file):
        """Generate the complete A5 PDF book with centered layout"""
        # Load sudoku data with updated keys
        with open(sudoku_json_file, 'r') as f:
            sudoku_data = json.load(f)
        
        # Create PDF with A5 page size
        canvas_obj = canvas.Canvas(output_file, pagesize=A5)
        
        page_num = 1
        for puzzle_id, puzzle_data in sudoku_data.items():
            self.create_centered_page(canvas_obj, puzzle_id, puzzle_data, page_num)
            canvas_obj.showPage()
            page_num += 1
        
        canvas_obj.save()
        print(f"A5 PDF generated with {page_num-1} pages: {output_file}")
        print(f"Page size: {self.page_width} x {self.page_height} points (A5)")

# Usage example
if __name__ == "__main__":
    # Custom A5 configuration for optimal layout
    a5_config = {
        'show_page_numbers': True,
        'show_qr_codes': True,
        'show_random_facts': True,
        'grid_size': 360,
        'cell_size': 40,
        'margin': 30,
        'title_font': 'Helvetica-Bold',
        'title_size': 18,
        'difficulty_font': 'Helvetica',
        'difficulty_size': 12,
        'fact_font': 'Helvetica',
        'fact_size': 8,
        'page_number_font': 'Helvetica',
        'page_number_size': 9,
        'qr_size': 45
    }
    
    generator = SudokuPDFGeneratorA5(a5_config)
    generator.generate_pdf('sudoku.json', 'sudoku_book_a5.pdf')
