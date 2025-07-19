import json
import qrcode
import randfacts
from io import BytesIO
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter


class RelativeSudokuPDFGenerator:
    def __init__(self, page_width_pt, page_height_pt, template_factors=None):
        """
        page_width_pt, page_height_pt: page size in points (1 pt = 1/72 inch)
        template_factors: dict of relative proportions (all values 0–1)
        """
        self.page_width = page_width_pt
        self.page_height = page_height_pt

        # Default proportional factors
        defaults = {
            "margin_h": 0.05,  # 5% of page width
            "margin_v": 0.10,  # 10% of page height
            "grid_scale": 0.80,  # grid occupies 100% of min(width,height)
            "title_height": 0.08,  # 8% of page height for title block
            "difficulty_height": 0.01,  # 5% of page height for difficulty text
            "qr_scale": 0.12,  # 12% of page width for QR-code
            "fact_height": 0.06,  # 6% of page height for fact area
            "page_num_height": 0.03,  # 3% of page height for page number area
            "font_title": 0.03,  # 5% of page height as font size
            "font_difficulty": 0.03,  # 3% of page height
            "font_number": 0.04,  # 4% of page height for grid numbers
            "font_fact": 0.02,  # 2.5% of page height
            "font_pagenum": 0.018,  # 2.5% of page height
        }
        self.factors = {**defaults, **(template_factors or {})}

    def generate_qr_image(self, puzzle_id):
        url = (
            "https://book.fastorial.dev/puzzle-books"
            "?category=sudoku"
            "&volume=1"
            f"&puzzle={puzzle_id}"
        )
        qr = qrcode.QRCode(box_size=2, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return ImageReader(buf)

    def get_random_fact(self):
        """
        Fetch random facts until one is ≤12 words.
        Returns the first valid fact, or an empty string if none found
        after max_attempts.
        """
        max_attempts = 100
        for _ in range(max_attempts):
            try:
                fact = randfacts.get_fact()
            except Exception:
                continue
            if len(fact.split()) <= 10:
                return fact
        # If no suitable fact found after retries, return a fallback short message
        return "Enjoy your Sudoku!"

    def compute_dimensions(self):
        f = self.factors
        pw, ph = self.page_width, self.page_height

        # Margins
        mh = pw * f["margin_h"]
        mv = ph * f["margin_v"]

        # Grid size: based on smaller of page dims
        grid_max = min(
            pw - 2 * mh,
            ph
            - 2 * mv
            - ph
            * (
                f["title_height"]
                + f["difficulty_height"]
                + f["fact_height"]
                + f["page_num_height"]
            ),
        )
        gs = grid_max * f["grid_scale"]

        # Positions
        x_center = pw / 2
        y_center = ph / 2

        header_y = ph - mv  # common top‐of‐page header Y

        dims = {
            "margin_h": mh,
            "margin_v": mv,
            "grid_size": gs,
            "cell_size": gs / 9,
            "header_y": header_y,
            "difficulty_y": ph - mv - ph * f["title_height"],
            "grid_x": (pw - gs) / 2,
            "grid_y": (ph - gs) / 2,
            "qr_size": pw * f["qr_scale"],
            "qr_x": pw - mh - pw * f["qr_scale"],
            "fact_y": mv + ph * f["page_num_height"],
            "page_num_y": mv / 2,
            "font_title": ph * f["font_title"],
            "font_diff": ph * f["font_difficulty"],
            "font_number": ph * f["font_number"],
            "font_fact": ph * f["font_fact"],
            "font_pagenum": ph * f["font_pagenum"],
        }

        # three vertical positions for difficulty badge:
        dims["diff_y_top"] = ph - mv - dims["font_diff"] / 2
        dims["diff_y_middle"] = ph / 2
        dims["diff_y_bottom"] = mv + dims["font_diff"] / 2

        return dims

    def draw_grid(self, c, grid, dims):
        cell = dims["cell_size"]
        x0, y0 = dims["grid_x"], dims["grid_y"]
        # grid lines
        for i in range(10):
            lw = 1.5 if i % 3 == 0 else 0.5
            c.setLineWidth(lw)
            x = x0 + i * cell
            c.line(x, y0, x, y0 + 9 * cell)
            y = y0 + i * cell
            c.line(x0, y, x0 + 9 * cell, y)
        # numbers
        c.setFont("Helvetica-Bold", dims["font_number"])
        for r in range(9):
            for col in range(9):
                v = grid[r][col]
                if v != 0:
                    cx = x0 + col * cell + cell / 2
                    cy = y0 + (8 - r) * cell + cell / 2 - dims["font_number"] / 3
                    c.drawCentredString(cx, cy, str(v))

    def draw_difficulty_badge(self, c, dims, difficulty_label, pnum):
        # Badge width is the vertical text height (font size), badge height is the vertical bar length
        # anushibin007 - We are hardcoding some values
        # here just so that we can have it constant for all the badges
        badge_width = dims["font_diff"] + 10
        badge_height = 75

        # Choose Y based on difficulty
        if difficulty_label.lower() == "easy":
            y = dims["diff_y_top"]
        elif difficulty_label.lower() == "medium":
            y = dims["diff_y_middle"]
        elif difficulty_label.lower() == "hard":
            y = dims["diff_y_bottom"]
        else:
            y = dims["diff_y_top"]  # fallback

        # For odd numbers, move badge flush to the right edge
        # Else, left side of the grid
        if pnum % 2 == 1:
            # The +2 is just to give that bleeding edge effect
            x = self.page_width - badge_width
        else:
            x = -2

        # Draw vertical badge (rotated)
        c.saveState()
        c.translate(x + badge_width / 2, y)
        c.rotate(90)
        c.setFillColor(self._badge_color(difficulty_label))
        c.rect(-badge_height / 2, -badge_width / 2, badge_height, badge_width, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", dims["font_diff"])
        c.drawCentredString(0, -badge_width * 0.2, difficulty_label.upper())
        c.restoreState()

    def _badge_color(self, label):
        return {"easy": colors.green, "medium": colors.orange, "hard": colors.red}.get(
            label.lower(), colors.gray
        )

    def wrap_text(self, c, txt, max_w, font, size):
        words, lines, line = txt.split(), [], ""
        for w in words:
            t = f"{line} {w}".strip()
            if c.stringWidth(t, font, size) <= max_w:
                line = t
            else:
                lines.append(line)
                line = w
        lines.append(line)
        return lines

    def add_qr_code_page(
        self,
        c,
        url,
        qr_size=4 * inch,
        title="Scan to visit our website",
    ):
        """
        Adds a new page to the ReportLab canvas `c` with a large, centered QR code.

        Args:
            c (canvas.Canvas): The ReportLab canvas object.
            url (str): The URL to encode in the QR code.
            page_width (float): Width of the page in points (default: letter width).
            page_height (float): Height of the page in points (default: letter height).
            qr_size (float): Size of the QR code square in points.
            title (str): Optional title to display above the QR code.
        """
        # Start a new page
        c.showPage()

        # Generate QR code image
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Save QR code image to BytesIO buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Wrap buffer in ImageReader for ReportLab
        qr_img = ImageReader(buffer)

        # Calculate position to center the QR code
        x = (self.page_width - qr_size) / 2
        y = (self.page_height - qr_size) / 2

        # Draw the QR code image on the canvas
        c.drawImage(qr_img, x, y, width=qr_size, height=qr_size, mask="auto")

        # Optionally, add a title or text above the QR code
        if title:
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(self.page_width / 2, y + qr_size + 30, title)

        # Print the URL at the bottom of the page
        # c.setFont("Helvetica", 18)
        # c.drawCentredString(self.page_width / 2, y - 30, url)

    def create_page(self, c, pid, pdata, pnum):
        dims = self.compute_dimensions()
        # Title (show the ID as title)
        c.setFont("Helvetica", dims["font_title"])
        c.drawCentredString(self.page_width / 2, dims["header_y"], f"{pid}")

        # ID & difficulty
        # c.setFont("Helvetica", dims['font_diff'])
        # c.drawCentredString(self.page_width/2, dims['difficulty_y'], f"{pid} ({pdata['d']})")

        # Date & Time Taken
        c.setFont("Helvetica", dims["font_diff"])
        c.drawCentredString(
            self.page_width / 2,
            dims["difficulty_y"] - 10,
            "Date: __________ Time taken: _____",
        )

        # Grid
        self.draw_grid(c, pdata["q"], dims)
        # QR
        # qr = self.generate_qr_image(pid)
        # c.drawImage(
        #         qr,
        #         dims['qr_x'],
        #         dims['header_y'] - dims['qr_size']/2 + dims['font_title']/2,
        #         width=dims['qr_size'],
        #         height=dims['qr_size'],
        #         mask='auto'
        #     )

        # Motivational Quote
        c.setFont("Helvetica-Oblique", dims["font_fact"])
        c.drawCentredString(
            self.page_width / 2, dims["margin_v"] - 15, f"{pdata['mq']}"
        )
        c.setFont("Helvetica", dims["font_fact"])
        c.drawCentredString(
            self.page_width / 2,
            dims["margin_v"] - 18 - dims["font_fact"],
            f" - {pdata['ma']}",
        )

        # Fact
        # lines = self.wrap_text(c, self.get_random_fact(), self.page_width-2*dims['margin_h'],
        #    "Helvetica-Oblique", dims['font_fact'])
        # c.setFont("Helvetica-Oblique", dims['font_fact'])
        # for i, ln in enumerate(lines):
        #     y = dims['fact_y'] + i*(dims['font_fact']+2)
        #     c.drawCentredString(self.page_width/2, y, ln)

        # Page #
        # c.setFont("Helvetica", dims['font_pagenum'])
        # c.drawCentredString(self.page_width/2, dims['page_num_y'], f"— {pnum} —")

        # ID - Not needed anymore because we are showing the ID on the top of the page
        # c.setFont("Helvetica", dims["font_pagenum"])
        # c.drawCentredString(self.page_width / 2, dims["page_num_y"], f"{pid}")

        # Badge on right edge of page
        self.draw_difficulty_badge(c, dims, pdata["d"], pnum)

    def draw_small_grid(self, c, grid, x0, y0, cell):
        """Draw a small solution grid."""
        for i in range(10):
            lw = 1 if i % 3 == 0 else 0.3
            c.setLineWidth(lw)
            xv = x0 + i * cell
            c.line(xv, y0, xv, y0 + 9 * cell)
            yh = y0 + i * cell
            c.line(x0, yh, x0 + 9 * cell, yh)
        font_size = cell * 0.6
        c.setFont("Helvetica", font_size)
        for r in range(9):
            for col in range(9):
                v = grid[r][col]
                cx = x0 + col * cell + cell / 2
                cy = y0 + (8 - r) * cell + cell / 2 - font_size / 3
                c.drawCentredString(cx, cy, str(v))

    def add_solutions_section(self, c, data, dims):
        """
        Render all solutions at the end:
        - Title page
        - 2 columns × 3 rows per page of small grids, each centered,
          with its puzzle ID above the grid.
        """
        # Title page
        c.setFont("Helvetica-Bold", dims["font_diff"])
        c.drawCentredString(
            self.page_width / 2, self.page_height - dims["margin_v"] + 15, "Solutions"
        )
        # c.showPage()

        sol_scale = 0.4
        sol_size = dims["grid_size"] * sol_scale
        sol_cell = sol_size / 9
        mh, mv = dims["margin_h"], dims["margin_v"]
        cols, rows = 2, 3

        # Compute slot widths/heights and offsets
        slot_w = (self.page_width - 2 * mh) / cols
        slot_h = (self.page_height - 2 * mv) / rows

        count = 0
        for pid, pdata in data.items():
            # New page after filling cols*rows slots
            if count and count % (cols * rows) == 0:
                c.showPage()

            col = count % cols
            row = (count // cols) % rows

            # Center of this slot
            cx = mh + slot_w * col + slot_w / 2
            cy = self.page_height - mv - slot_h * row - slot_h / 2

            # Draw puzzle ID above grid
            c.setFont("Helvetica", dims["font_diff"])
            text_y = cy + sol_size / 2 + dims["font_diff"] + 2
            c.drawCentredString(cx, text_y, pid)

            # Top-left corner of grid
            x0 = cx - sol_size / 2
            y0 = cy - sol_size / 2

            # Draw the small solution grid
            self.draw_small_grid(c, pdata["a"], x0, y0, sol_cell)

            count += 1

        # Use this if you need an extra page after all the solutions
        # c.showPage()

    def generate_pdf(self, json_file, output_pdf):
        with open(json_file) as f:
            data = json.load(f)
        c = canvas.Canvas(output_pdf, pagesize=(self.page_width, self.page_height))
        dims = self.compute_dimensions()
        page = 1
        # Draw puzzles
        for pid, pdata in data.items():
            self.create_page(c, pid, pdata, page)
            c.showPage()
            page += 1
        # Draw solutions at end
        self.add_solutions_section(c, data, dims)
        self.add_qr_code_page(
            c,
            "https://books.fastorial.dev/?utm_source=book&utm_medium=qr_code&utm_campaign=sdku-v1",
            qr_size=4 * inch,
            title="Scan for more puzzles and fun",
        )
        c.save()
        print(f"Generated: {output_pdf}")


def append_covers(
    front_cover_path, preface_page, main_pdf_path, back_cover_path, output_pdf_path
):
    writer = PdfWriter()

    # Add front cover
    with open(front_cover_path, "rb") as f_front:
        front_reader = PdfReader(f_front)
        for page in front_reader.pages:
            writer.add_page(page)

    # Add preface pages
    with open(preface_page, "rb") as f_front:
        preface_page_reader = PdfReader(f_front)
        for page in preface_page_reader.pages:
            writer.add_page(page)

    # Add main book
    with open(main_pdf_path, "rb") as f_main:
        main_reader = PdfReader(f_main)
        for page in main_reader.pages:
            writer.add_page(page)

    # Add back cover
    with open(back_cover_path, "rb") as f_back:
        back_reader = PdfReader(f_back)
        for page in back_reader.pages:
            writer.add_page(page)

    # Write the final PDF
    with open(output_pdf_path, "wb") as f_out:
        writer.write(f_out)


# Example usage:
if __name__ == "__main__":
    # e.g. 4.25"×6.87" → (4.25*72, 6.87*72)
    W, H = 4.25 * inch, 6.87 * inch
    # W, H = 3*inch, 4*inch
    gen = RelativeSudokuPDFGenerator(W, H)
    gen.generate_pdf("../generated-mixed.json", "generated-puzzles-content.pdf")

    # Append covers and other premade pages
    premade_pages_root_dir = "./premade"
    front_cover = f"{premade_pages_root_dir}/Book Cover - Front.pdf"
    preface_page = f"{premade_pages_root_dir}/Preface.pdf"
    main_pdf = "generated-puzzles-content.pdf"
    back_cover = f"{premade_pages_root_dir}/Book Cover - Back.pdf"

    # Final merged PDF
    output_pdf = "generated-sudoku.pdf"

    append_covers(front_cover, preface_page, main_pdf, back_cover, output_pdf)
