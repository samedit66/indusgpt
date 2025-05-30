from fpdf import FPDF

from src import types


class PdfProcessor:
    """Processor that generates PDF reports from Q&A data."""

    def __init__(self, output_path: str | None = None):
        """Initialize the PDF processor.

        Args:
            output_path: Optional path where to save the PDF. If not provided,
                        the processor will return the PDF object instead of saving.
        """
        self.output_path = output_path

    def _create_pdf(self) -> FPDF:
        """Create and configure a new PDF document."""
        # Use A4 format with larger margins for better readability
        pdf = FPDF(format="A4")
        # Set margins (left, top, right) in mm
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        return pdf

    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing extra whitespace and newlines.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Replace multiple spaces and newlines with single space
        return " ".join(text.split())

    def _write_text_block(
        self, pdf: FPDF, text: str, effective_width: float, line_height: float
    ) -> None:
        """Write a block of text to PDF with proper wrapping.

        Args:
            pdf: PDF document
            text: Text to write
            effective_width: Available width for text
            line_height: Height of each line
        """
        # Normalize and split text into words
        text = self._normalize_text(text)
        words = text.split()

        current_line = []
        current_width = 0

        for word in words:
            # Get width of word plus space
            word_width = pdf.get_string_width(word + " ")

            if current_width + word_width <= effective_width:
                current_line.append(word)
                current_width += word_width
            else:
                # Write current line
                if current_line:
                    pdf.cell(
                        effective_width, line_height, " ".join(current_line), ln=True
                    )
                # Start new line with current word
                current_line = [word]
                current_width = word_width

        # Write last line if any
        if current_line:
            pdf.cell(effective_width, line_height, " ".join(current_line), ln=True)

    def _add_user_qa_section(
        self, pdf: FPDF, user_id: int, qa_pairs: list[types.QaPair]
    ) -> None:
        """Add a user's Q&A section to the PDF.

        Args:
            pdf: The PDF document to add to
            user_id: The ID of the user whose Q&A pairs are being added
            qa_pairs: List of question-answer pairs to add
        """
        # Add user header
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, f"User ID: {user_id}", ln=True)
        pdf.ln(5)

        effective_width = pdf.w - pdf.l_margin - pdf.r_margin
        line_height = 7  # Reduced from 10 for better spacing

        for qa in qa_pairs:
            # Question
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(0, 0, 255)  # Blue for questions
            self._write_text_block(
                pdf, f"Q: {qa.question.text}", effective_width, line_height
            )

            # Small spacing between Q and A
            pdf.ln(2)

            # Answer
            pdf.set_text_color(0, 0, 0)  # Black for answers
            pdf.set_font("helvetica", "", 12)
            self._write_text_block(pdf, f"A: {qa.answer}", effective_width, line_height)

            # Space between Q&A pairs
            pdf.ln(7)

            # Check if we need a new page
            if pdf.get_y() > pdf.page_break_trigger:
                pdf.add_page()

    async def __call__(self, user_id: int, qa_pairs: list[types.QaPair]) -> FPDF | None:
        """Process Q&A pairs by creating a PDF report for a single user.

        Args:
            user_id: The ID of the user whose Q&A pairs are being processed
            qa_pairs: List of question-answer pairs to process

        Returns:
            FPDF object if output_path is None, otherwise None after saving the PDF
        """
        pdf = self._create_pdf()
        self._add_user_qa_section(pdf, user_id, qa_pairs)

        if self.output_path:
            pdf.output(self.output_path)
            return None
        return pdf

    async def process_multiple(
        self, qa_data: dict[int, list[types.QaPair]]
    ) -> FPDF | None:
        """Process Q&A pairs for multiple users into a single PDF report.

        Args:
            qa_data: Dictionary mapping user IDs to their Q&A pairs

        Returns:
            FPDF object if output_path is None, otherwise None after saving the PDF
        """
        pdf = self._create_pdf()

        # Add title
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "User Q&A Report", ln=True, align="C")
        pdf.ln(10)

        # Add each user's section
        for user_id, qa_pairs in qa_data.items():
            self._add_user_qa_section(pdf, user_id, qa_pairs)
            # Don't add a page after the last user
            if user_id != list(qa_data.keys())[-1]:
                pdf.add_page()

        if self.output_path:
            pdf.output(self.output_path)
            return None
        return pdf
