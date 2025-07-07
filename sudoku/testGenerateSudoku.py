import unittest
import copy

# Import functions from your generator script
from generateSudoku import (
    is_valid,
    solve_sudoku,
    generate_complete_sudoku,
    remove_cells,
    board_to_question,
    generate_sudoku_puzzle,
    generate_sudoku_set,
    count_solutions
)

class TestSudokuGenerator(unittest.TestCase):
    def test_generate_complete_sudoku_valid(self):
        board = generate_complete_sudoku()
        # Check all numbers 1-9 appear in each row, column, and box
        for i in range(9):
            self.assertEqual(set(board[i]), set(range(1, 10)))
            self.assertEqual(set(row[i] for row in board), set(range(1, 10)))
        # Check boxes
        for box_row in range(3):
            for box_col in range(3):
                nums = set()
                for i in range(3):
                    for j in range(3):
                        nums.add(board[box_row*3 + i][box_col*3 + j])
                self.assertEqual(nums, set(range(1, 10)))

    def test_is_valid(self):
        board = generate_complete_sudoku()
        # Placing any number already in row/col/box should be invalid
        self.assertFalse(is_valid(board, 0, 0, board[0][1]))
        self.assertFalse(is_valid(board, 0, 0, board[1][0]))
        self.assertFalse(is_valid(board, 0, 0, board[1][1]))
        # Placing a number not in row/col/box should be valid
        unused = set(range(1, 10)) - {board[0][i] for i in range(9)} - {board[i][0] for i in range(9)}
        if unused:
            num = unused.pop()
            self.assertTrue(is_valid([[0]*9 for _ in range(9)], 0, 0, num))

    def test_solve_sudoku(self):
        board = generate_complete_sudoku()
        puzzle = copy.deepcopy(board)
        # Remove a few cells
        for i in range(3):
            puzzle[i][i] = 0
        self.assertTrue(solve_sudoku(puzzle))
        self.assertEqual(puzzle, board)

    def test_remove_cells_difficulty(self):
        board = generate_complete_sudoku()
        for difficulty, clue_range in [('easy', (45, 50)), ('medium', (35, 40)), ('hard', (25, 30))]:
            puzzle = copy.deepcopy(board)
            puzzle = remove_cells(puzzle, difficulty)
            num_clues = sum(cell != 0 for row in puzzle for cell in row)
            self.assertGreaterEqual(num_clues, clue_range[0])
            self.assertLessEqual(num_clues, clue_range[1])
            # Ensure unique solution
            self.assertEqual(count_solutions(puzzle), 1)

    def test_board_to_question_format(self):
        board = generate_complete_sudoku()
        puzzle = copy.deepcopy(board)
        puzzle[0][0] = 0
        question = board_to_question(puzzle)
        self.assertEqual(question[0][0], 0)
        for i in range(1, 9):
            self.assertIsInstance(question[0][i], int)

    def test_generate_sudoku_puzzle_and_set(self):
        question, answer = generate_sudoku_puzzle('easy')
        self.assertEqual(len(question), 9)
        self.assertEqual(len(answer), 9)
        self.assertTrue(all(len(row) == 9 for row in question))
        self.assertTrue(all(len(row) == 9 for row in answer))
        # answer should be a valid sudoku
        for i in range(9):
            self.assertEqual(set(answer[i]), set(range(1, 10)))
        # test set generation
        puzzles = generate_sudoku_set(3, 'hard')
        self.assertEqual(len(puzzles), 3)
        for key, val in puzzles.items():
            self.assertIn('q', val)
            self.assertIn('a', val)
            self.assertIn('d', val)
            self.assertEqual(val['d'], 'hard')

    def test_invalid_arguments(self):
        # Simulate invalid argument handling
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, 'generateSudoku.py'],
            input='',
            capture_output=True,
            text=True
        )
        self.assertIn("Usage", result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
