import reedsolo
from PIL import Image
import numpy as np

def char_count_indicator(qr_string):
    bin_len = bin(len(qr_string))[2:].zfill(8)
    return bin_len

def str_to_bin(str):
    bin_str = ""
    for i in str:
        ascii_val = ord(i)
        #print("ASCII:", ascii_val)

        bin_val = bin(ascii_val)[2:].zfill(8)
        #print("\nBINARY:", bin_val)
        
        bin_str = bin_str + "" + bin_val

    return bin_str.strip()

def pad_bytes(encoded_str):
    num_pad = (440 - len(encoded_str)) // 8 # 440 is the total number of codewords for 3-L

    padding = ""
    for i in range(num_pad):
        if i % 2 == 0:
            padding += "11101100" # 236
        else:
            padding += "00010001" # 17
    
    return padding

def add_error_correction(data, total_codewords):
    rs = reedsolo.RSCodec(total_codewords - len(data) // 8)
    data_bytes = int(data, 2).to_bytes((len(data) + 7) // 8, "big")
    encoded_data = rs.encode(data_bytes)

    # Convert back to binary string
    bin_str = ""
    for byte in encoded_data:
        bin_str += bin(byte)[2:].zfill(8)
    return bin_str


def create_alignment_matrix():
    size = 29  # Calculate matrix size
    matrix = [[None for _ in range(size)] for _ in range(size)]

    # Add finder patterns (top-left, top-right, bottom-left)
    def add_finder_pattern(row, col):
        for r in range(-1, 8):
            for c in range(-1, 8):
                if 0 <= row + r < size and 0 <= col + c < size:
                    if 0 <= r <= 6 and 0 <= c <= 6:  # Finder pattern area
                        if 2 <= r <= 4 and 2 <= c <= 4:  # Center 3x3 block
                            matrix[row + r][col + c] = 1
                        elif r in {0, 6} or c in {0, 6}:  # Outer dark border
                            matrix[row + r][col + c] = 1
                        else:  # White area
                            matrix[row + r][col + c] = 0
                    else:  # Border around the finder
                        matrix[row + r][col + c] = 0

    add_finder_pattern(0, 0)  # Top-left
    add_finder_pattern(0, size - 7)  # Top-right
    add_finder_pattern(size - 7, 0)  # Bottom-left

    # Add timing patterns
    for i in range(8, size - 8):
        matrix[6][i] = 1 if i % 2 == 0 else 0  # Horizontal
        matrix[i][6] = 1 if i % 2 == 0 else 0  # Vertical

    # Add alignment pattern (for Version 3, one at [22, 22])
    for r in range(-2, 3):
        for c in range(-2, 3):
            if 0 <= 22 + r < size and 0 <= 22 + c < size:
                if r == 0 and c == 0:  # Center
                    matrix[22 + r][22 + c] = 1
                elif r in {-2, 2} or c in {-2, 2}:  # Outer square
                    matrix[22 + r][22 + c] = 1
                else:  # White area
                    matrix[22 + r][22 + c] = 0

    #add_alignment_pattern(22, 22)

    # Dark pixel
    matrix[21][8] = 1

    # Add format information
    format_data = "111011111000100"
    reversed_data = format_data[::-1]  # Reverse the data for easier processing
    bot_rfd = reversed_data[8:]

    top_fd = format_data[9:]
    r_top_fd = top_fd[::-1]

    right_fd = format_data[7:]

    # Top-left
    for i in range(7):
        if i < 6:
            matrix[8][i] = int(format_data[i])
        matrix[i+22][8] = int(bot_rfd[i])

    # Top-left corner (6, 7, 8)
    matrix[8][7] = int(format_data[6])
    matrix[8][8] = int(format_data[7])
    matrix[8-1][8] = int(format_data[8])

    # Top-right (9-14)
    for i in range(6):
        matrix[i][8] = int(r_top_fd[i])

    # Top-left (7-14)
    for i in range(8):
        matrix[8][21+i] = int(right_fd[i])


    return matrix
'''

def man_matrix(version):
    dim = 29

    np.array([[0 for _ in range(dim)] for _ in range(dim)])
'''

def render_matrix_as_image(matrix, box_size, file_name):
    size = len(matrix)
    img = Image.new("RGB", (size * box_size, size * box_size), "white")
    pixels = img.load()

    for i in range(size):
        for j in range(size):
            if matrix[i][j] == 1:  # Black modules
                color = (0, 0, 0)  # Black
            elif matrix[i][j] == 0:  # White modules
                color = (255, 255, 255)  # White
            else:  # None (unassigned areas)
                color = (128, 128, 128)  # Gray
            for x in range(box_size):
                for y in range(box_size):
                    pixels[j * box_size + x, i * box_size + y] = color

    img.save(file_name)
    print("QR Matrix outline saved as", file_name)


qr_string = "https://mountainlionmovies.com"

mi = "0100"
cci = char_count_indicator(qr_string)
encoded_str = str_to_bin(qr_string)

terminator = "0000"

total = mi + cci + encoded_str + terminator

pb = pad_bytes(total)

total = total + pb

# FOR 3-L: Total Codewords Num = 440
print("TOTAL:", total)
print("TOTAL LEN:", len(total))

total_codewords = 55

result = add_error_correction(total, total_codewords)

print("RESULT:", result)
print("RESULT LEN:", len(result))


matrix = create_alignment_matrix()
print(np.array(matrix))

render_matrix_as_image(matrix, box_size=20, file_name="qrcode/qr_matrix.png")
