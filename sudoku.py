import argparse

from Tkinter import Tk, Canvas, Frame, Button, BOTH, TOP, BOTTOM
from copy import deepcopy

LEVELS = ['easy', 'medium', 'hard']  # Available sudoku boards
MARGIN = 20  # Pixels around the board
SIDE = 50  # Width of every board cell.
WIDTH = HEIGHT = MARGIN * 2 + SIDE * 9  # Width and height of the whole board

def parse_arguments():
	arg_parser = argparse.ArgumentParser()
	arg_parser.add_argument("--level", choices=LEVELS, required=True)
	args = vars(arg_parser.parse_args())
	return args['level']

class SudokuBoard(object):

	def __init__(self, board_file):
		self.board = self.__create_board(board_file)

	def __create_board(self, board_file):
		board = []
		for line in board_file:
			line = line.strip()		# Removes newline character from board_file
			if len(line) != 9:
				raise SudokuError("Each line in the sudoku puzzle must be 9 chars long.")
			board.append([])

			for c in line:
				if not c.isdigit():
					raise SudokuError("Valid characters for a sudoku puzzle must be in 0-9")
				board[-1].append(int(c))	

		if len(board) != 9:
			raise SudokuError("Each sudoku puzzle must be 9 lines long")
		return board

class SudokuUI(Frame):

	def __init__(self, parent, game):
		self.game = game
		Frame.__init__(self, parent)
		self.parent = parent
		self.row, self.col = -1, -1
		self.__initUI()

	def __initUI(self):
		self.parent.title("Sudoku")
		self.pack(fill=BOTH)
		self.canvas = Canvas(self,width=WIDTH,height=HEIGHT)
		self.canvas.pack(fill=BOTH, side=TOP)
		clear_button = Button(self,text="Clear answers",command=self.__clear_answers)
		clear_button.pack(fill=BOTH, side=BOTTOM)
		solve_button = Button(self,text="Solve Puzzle",command=self.__solve_complete_puzzle)
		solve_button.pack(fill=BOTH, side=BOTTOM)
		self.__draw_grid()
		self.__draw_puzzle()
		self.canvas.bind("<Button-1>", self.__cell_clicked)
		self.canvas.bind("<Key>", self.__key_pressed)

	def __draw_grid(self):
		for i in xrange(10):
			color = "blue" if i % 3 == 0 else "gray"
			x0 = MARGIN + i * SIDE
			y0 = MARGIN
			x1 = MARGIN + i * SIDE
			y1 = HEIGHT - MARGIN
			self.canvas.create_line(x0, y0, x1, y1, fill=color)
			x0 = MARGIN
			y0 = MARGIN + i * SIDE
			x1 = WIDTH - MARGIN
			y1 = MARGIN + i * SIDE
			self.canvas.create_line(x0, y0, x1, y1, fill=color)

	def __draw_puzzle(self):
		for i in xrange(9):
			for j in xrange(9):
				answer = self.game.puzzle[i][j]
				if answer != 0:
					x = MARGIN + j * SIDE + SIDE / 2
					y = MARGIN + i * SIDE + SIDE / 2
					original = self.game.start_puzzle[i][j]
					color = "black" if answer == original else "sea green"
					self.canvas.create_text(x, y, text=answer, fill=color)

	def __draw_cursor(self):
		if self.row >= 0 and self.col >= 0:
			x0 = MARGIN + self.col * SIDE + 1
			y0 = MARGIN + self.row * SIDE + 1
			x1 = MARGIN + (self.col + 1) * SIDE - 1
			y1 = MARGIN + (self.row + 1) * SIDE - 1
			self.canvas.create_rectangle(x0, y0, x1, y1,outline="red")

	def __draw_victory(self):
		x0 = y0 = MARGIN + SIDE * 2
		x1 = y1 = MARGIN + SIDE * 7
		self.canvas.create_oval(x0, y0, x1, y1, tags="victory", fill="dark orange", outline="orange")
		x = y = MARGIN + 4 * SIDE + SIDE / 2
		self.canvas.create_text(x, y,text="You win!", tags="victory",fill="white", font=("Arial", 32))

	def __cell_clicked(self, event):
		if self.game.game_over:
			return
		x, y = event.x, event.y
		if (MARGIN < x < WIDTH - MARGIN and MARGIN < y < HEIGHT - MARGIN):
			self.canvas.focus_set()
			# get row and col numbers from x,y coordinates
			row, col = (y - MARGIN) / SIDE, (x - MARGIN) / SIDE
			# if cell was selected already - deselect it
			if (row, col) == (self.row, self.col):
				self.row, self.col = -1, -1
			elif self.game.puzzle[row][col] == 0:
				self.row, self.col = row, col
		else:
			self.row, self.col = -1, -1

		self.__draw_cursor()

	def __key_pressed(self, event):
		if self.game.game_over:
			return
		if self.row >= 0 and self.col >= 0 and event.char in "1234567890":
			self.game.puzzle[self.row][self.col] = int(event.char)
			self.col, self.row = -1, -1
			self.__draw_puzzle()
			self.__draw_cursor()
			if self.game.check_win():
				self.__draw_victory()
	
	def __clear_answers(self):
		self.game.start()
		self.canvas.delete("victory")
		self.__draw_puzzle()

	def __solve_complete_puzzle(self):
		self.puzzle = deepcopy(self.game.puzzle)
		solution_exist = SudokuBackTrack(self.puzzle).sol_exist
		if solution_exist:
			self.__draw_complete_puzzle()
		else:
			self.__print_invalid_puzzle()
			
	def __draw_complete_puzzle(self):
		for i in xrange(9):
			for j in xrange(9):
				answer = self.puzzle[i][j]
				original = self.game.puzzle[i][j]
				x = MARGIN + j * SIDE + SIDE / 2
				y = MARGIN + i * SIDE + SIDE / 2
				color = "black" if answer == original else "sea green"
				self.canvas.create_text(x, y, text=answer, fill=color)	

	def __print_invalid_puzzle(self):
		x0 = y0 = MARGIN + SIDE * 2
		x1 = y1 = MARGIN + SIDE * 7
		self.canvas.create_oval(x0, y0, x1, y1, tags="victory", fill="dark orange", outline="orange")
		x = y = MARGIN + 4 * SIDE + SIDE / 2
		self.canvas.create_text(x, y,text="Solution does not \n          Exist!", tags="victory",fill="white", font=("Arial", 20))


class SudokuBackTrack(object):

	def __init__(self,puzzle):
		self.puzzle = puzzle
		self.sol_exist = self.__backtrack(puzzle)
		
	def __backtrack(self, puzzle):
		b=[0,0]	
		if not self.__check_puzzle_complete(puzzle,b):
			return True	
		b_row = b[0]
		b_col = b[1]
		for num in range(1,10):
			if self.__is_safe(puzzle, b_row, b_col, num):
				puzzle[b_row][b_col] = num
				if self.__backtrack(puzzle):
					return True
				puzzle[b_row][b_col] = 0
		return False
	
	def __check_puzzle_complete(self, puzzle, b):
		for row in range(9):
			for col in range(9):
				if puzzle[row][col]==0:
					b[0]= row
					b[1] = col
					return True
		return False

	def __used_in_row(self, puzzle, row, num):
		for col in range(9):
			if puzzle[row][col]==num:
				return True
		return False

	def __used_in_column(self, puzzle, col, num):
		for row in range(9):
			if puzzle[row][col]==num:
				return True
		return False	

	def __used_in_box(self, puzzle, box_start, box_end, num):
		for row in range(3):
			for col in range(3):
				if puzzle[row + box_start][col + box_end]==num:
					return True
		return False

	def __is_safe(self, puzzle, row, col, num):
		return not self.__used_in_row(puzzle,row,num) and not self.__used_in_column(puzzle,col,num) and not self.__used_in_box(puzzle,row - row%3, col - col%3, num)	


class SudokuGame(object):

	def __init__(self, board_file):
		self.board_file = board_file
		self.start_puzzle = SudokuBoard(board_file).board

	def start(self):
		self.game_over = False
		self.puzzle = deepcopy(self.start_puzzle)
		
	def check_win(self):
		for row in xrange(9):
			if not self.__check_row(row):
				return False
		for column in xrange(9):
			if not self.__check_column(column):
				return False
		for row in xrange(3):
			for column in xrange(3):
				if not self.__check_square(row, column):
					return False
		self.game_over = True
		return True

	def __check_block(self, block):
		return set(block) == set(range(1, 10))

	def __check_row(self, row):
		return self.__check_block(self.puzzle[row])

	def __check_column(self, column):
		return self.__check_block([self.puzzle[row][column] for row in xrange(9)])

	def __check_square(self, row, column):
		return self.__check_block([self.puzzle[r][c]for r in xrange(row * 3, (row + 1) * 3)for c in xrange(column * 3, (column + 1) * 3)])

if __name__ == '__main__':
	
	level_name = parse_arguments()
	with open('%s.txt' % level_name, 'r') as levels_name:
		game = SudokuGame(levels_name)
		game.start()
		root = Tk()
		SudokuUI(root, game)
		root.geometry("%dx%d" % (WIDTH, HEIGHT + 80))
		root.mainloop()