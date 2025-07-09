import sys
import random
import json
import copy

HELP_PROMPT = """
Sudoku Generator Script Usage:

python script.py <count> <difficulty>

  <count>      : Number of puzzles to generate (e.g., 100)
  <difficulty> : One of 'easy', 'medium', or 'hard'

Example:
  python script.py 5 medium

The script will output a JSON array of sudoku puzzles with the specified count and difficulty.
"""

def is_valid(board, row, col, num):
    for x in range(9):
        if board[row][x] == num or board[x][col] == num:
            return False
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True

def solve_sudoku(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for num in range(1, 10):
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        if solve_sudoku(board):
                            return True
                        board[row][col] = 0
                return False
    return True

def fill_diagonal_boxes(board):
    for k in range(0, 9, 3):
        nums = list(range(1, 10))
        random.shuffle(nums)
        for i in range(3):
            for j in range(3):
                board[k+i][k+j] = nums.pop()

def fill_remaining(board, i, j):
    if j >= 9 and i < 8:
        i += 1
        j = 0
    if i >= 9 and j >= 9:
        return True
    if i < 3:
        if j < 3:
            j = 3
    elif i < 6:
        if j == int(i / 3) * 3:
            j += 3
    else:
        if j == 6:
            i += 1
            j = 0
            if i >= 9:
                return True
    for num in range(1, 10):
        if is_valid(board, i, j, num):
            board[i][j] = num
            if fill_remaining(board, i, j+1):
                return True
            board[i][j] = 0
    return False

def generate_complete_sudoku():
    board = [[0]*9 for _ in range(9)]
    fill_diagonal_boxes(board)
    fill_remaining(board, 0, 3)
    return board

def count_solutions(board):
    count = 0
    def solve_count(b):
        nonlocal count
        for row in range(9):
            for col in range(9):
                if b[row][col] == 0:
                    for num in range(1, 10):
                        if is_valid(b, row, col, num):
                            b[row][col] = num
                            solve_count(b)
                            b[row][col] = 0
                    return
        count += 1
    solve_count(copy.deepcopy(board))
    return count

def remove_cells(board, difficulty):
    if difficulty == 'easy':
        clues = random.randint(45, 50)
    elif difficulty == 'medium':
        clues = random.randint(35, 40)
    else:
        clues = random.randint(25, 30)
    cells_to_remove = 81 - clues
    while cells_to_remove > 0:
        row = random.randint(0, 8)
        col = random.randint(0, 8)
        if board[row][col] != 0:
            backup = board[row][col]
            board[row][col] = 0
            if count_solutions(board) != 1:
                board[row][col] = backup
            else:
                cells_to_remove -= 1
    return board

def board_to_question(board):
    return [[cell if cell != 0 else 0 for cell in row] for row in board]

def generate_sudoku_puzzle(difficulty):
    complete = generate_complete_sudoku()
    puzzle = copy.deepcopy(complete)
    puzzle = remove_cells(puzzle, difficulty)
    question = board_to_question(puzzle)
    return question, complete

def generate_sudoku_set(count, difficulty):
    result = {}
    for i in range(1, count+1):
        question, answer = generate_sudoku_puzzle(difficulty)
        key = f"sdku-v1-q{i}"
        result[key] = {
            "q": question,
            "a": answer,
            "d": difficulty
        }
    return result

def main():
    if len(sys.argv) != 3:
        print(HELP_PROMPT)
        sys.exit(1)
    try:
        count = int(sys.argv[1])
        difficulty = sys.argv[2].lower()
        if difficulty not in ['easy', 'medium', 'hard']:
            print(HELP_PROMPT)
            sys.exit(1)
    except Exception:
        print(HELP_PROMPT)
        sys.exit(1)

    puzzles = generate_sudoku_set(count, difficulty)
    print(json.dumps(puzzles, indent=2))

if __name__ == "__main__":
    main()
