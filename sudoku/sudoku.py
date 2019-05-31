import dimod
import math
import string

from dimod.generators.constraints import combinations
from hybrid.reference import KerberosSampler


def get_label(row, col, digit):
    return "{row},{col}_{digit}".format(**locals())


def get_matrix(filename):
    try:
        with open(filename, "r") as f:
            content = f.readlines()
    except FileNotFoundError:
        raise

    lines = []
    for line in content:
        new_line = line.rstrip()    # Strip whitespace

        if new_line:
            new_line = list(new_line.split(' ')) #TODO: to upper
            lines.append(new_line)

    return lines


def is_correct(matrix):
    n = len(matrix)        # Number of rows/columns
    m = int(math.sqrt(n))  # Number of subsquare rows/columns
    digits = list(string.digits + string.ascii_uppercase)[1:n+1]
    solution = set(digits)  # Digits in a solution

    # Verifying rows
    for row in matrix:
        if set(row) != solution:
            print("Error in row: ", row)
            return False

    # Verifying columns
    for j in range(n):
        col = [matrix[i][j] for i in range(n)]
        if set(col) != solution:
            print("Error in col: ", col)
            return False

    # Verifying subsquares
    subsquare_coords = [(i, j) for i in range(m) for j in range(m)]
    for r_scalar in range(m):
        for c_scalar in range(m):
            subsquare = [matrix[i + r_scalar * m][j + c_scalar * m] for i, j
                         in subsquare_coords]
            if set(subsquare) != solution:
                print("Error in subsquare: ", subsquare)
                return False

    return True


#TODO pass keyword args to kerberos
def main():
    filename = "problem_16x16.txt"
    matrix = get_matrix(filename)

    # Set up
    n = len(matrix)          # Number of rows/columns in sudoku
    m = int(math.sqrt(n))    # Number of rows/columns in sudoku subsquare
    digits = list(string.digits + string.ascii_uppercase)[1:n+1]

    bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, dimod.SPIN)

    # Constraint: Each node can only select one digit
    for row in range(n):
        for col in range(n):
            node_digits = [get_label(row, col, digit) for digit in digits]
            one_digit_bqm = combinations(node_digits, 1)
            bqm.update(one_digit_bqm)

    # Constraint: Each row of nodes cannot have duplicate digits
    for row in range(n):
        for digit in digits:
            row_nodes = [get_label(row, col, digit) for col in range(n)]
            row_bqm = combinations(row_nodes, 1)
            bqm.update(row_bqm)

    # Constraint: Each column of nodes cannot have duplicate digits
    for col in range(n):
        for digit in digits:
            col_nodes = [get_label(row, col, digit) for row in range(n)]
            col_bqm = combinations(col_nodes, 1)
            bqm.update(col_bqm)

    # Constraint: Each sub-square cannot have duplicates
    # Build indices of a basic subsquare
    subsquare_indices = [(row, col) for row in range(m) for col in range(m)]

    # Build full sudoku array
    for r_scalar in range(m):
        for c_scalar in range(m):
            for digit in digits:
                # Shifts for moving subsquare inside sudoku matrix
                row_shift = r_scalar * m
                col_shift = c_scalar * m

                # Build the labels for a subsquare
                subsquare = [get_label(row + row_shift, col + col_shift, digit)
                             for row, col in subsquare_indices]
                subsquare_bqm = combinations(subsquare, 1)
                bqm.update(subsquare_bqm)

    # Constraint: Fix known values
    for row, line in enumerate(matrix):
        for col, value in enumerate(line):
            if value != '0':
                bqm.fix_variable(get_label(row, col, value), 1)

    # Solve BQM
    solution = KerberosSampler().sample(bqm, max_iter=40, convergence=6)
    best_solution = solution.first.sample

    # Print solution
    solution_list = [k for k, v in best_solution.items() if v == 1]

    for label in solution_list:
        coord, digit = label.split('_')
        row, col = map(int, coord.split(','))
        matrix[row][col] = digit

    for line in matrix:
        printable_line = " ".join(line)
        print(printable_line)

    # Verify
    if is_correct(matrix):
        print("The solution is correct")
    else:
        print("The solution is incorrect")


if __name__ == "__main__":
    main()

