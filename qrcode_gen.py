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

def hex_to_dec_list(hex_str):
    dec_str = []
    for i in range(0, len(hex_str), 2):
        dec_str.append(int(hex_str[i:i+2], 16))
    
    return dec_str

def add_error_correction(dec_list, total_codewords):
    rs = reedsolo.RSCodec(15)
    encoded_data = rs.encode(dec_list)
    print("ENCODED DATA:", encoded_data)

    # Convert back to binary string
    bin_str = ''.join(format(byte, '08b') for byte in encoded_data)
    return bin_str

# 0 = 2; 1 = 3
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
                            matrix[row + r][col + c] = 3
                        elif r in {0, 6} or c in {0, 6}:  # Outer dark border
                            matrix[row + r][col + c] = 3
                        else:  # White area
                            matrix[row + r][col + c] = 2
                    else:  # Border around the finder
                        matrix[row + r][col + c] = 2

    add_finder_pattern(0, 0)  # Top-left
    add_finder_pattern(0, size - 7)  # Top-right
    add_finder_pattern(size - 7, 0)  # Bottom-left

    # Add timing patterns
    for i in range(8, size - 8):
        matrix[6][i] = 3 if i % 2 == 0 else 2  # Horizontal
        matrix[i][6] = 3 if i % 2 == 0 else 2  # Vertical

    # Add alignment pattern (for Version 3, one at [22, 22])
    for r in range(-2, 3):
        for c in range(-2, 3):
            if 0 <= 22 + r < size and 0 <= 22 + c < size:
                if r == 0 and c == 0:  # Center
                    matrix[22 + r][22 + c] = 3
                elif r in {-2, 2} or c in {-2, 2}:  # Outer square
                    matrix[22 + r][22 + c] = 3
                else:  # White area
                    matrix[22 + r][22 + c] = 2

    #add_alignment_pattern(22, 22)

    # Dark pixel
    matrix[21][8] = 3

    # Add format information
    l_zero = "111011111000100"
    l_one =  "111001011110011"
    #format_data = "333233333222322"
    current_mask = l_one

    int_fd = [int(char) + 2 for char in current_mask]
    format_data = ''.join(str(num) for num in int_fd)

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


def encode_matrix(matrix, data):
    size = 29
    dim = size - 1

    test_data = "0101"

    # Encoded Label
    idx = 0
    for i in range(2):
        for j in range(2):
            matrix[dim-i][dim-j] = int(data[idx])
            idx += 1

    
    # Char Count Indicator
    idx = 4
    for i in range(4):
        for j in range(2):
            matrix[(dim-2)-i][dim-j] = int(data[idx])
            idx += 1

    # Data ...


    return matrix

def test_encode_matrix(matrix, data):
    size = 29
    row = size - 1  # Start from the bottom-right
    col = size - 1  # Start with the last column
    direction = -1  # Moving up initially
    data_index = 0  # Track the current bit of the encoded data

    while col > 0:
        # Skip the vertical timing column
        if col == 6:
            col -= 1

        for _ in range(size):
            # Place data in the right column of the pair
            if matrix[row][col] is None and data_index < len(data):
                matrix[row][col] = int(data[data_index])
                data_index += 1

            # Move to the left column of the pair
            if col > 0 and matrix[row][col - 1] is None and data_index < len(data):
                matrix[row][col - 1] = int(data[data_index])
                data_index += 1

            # Move up or down depending on direction
            row += direction

            # If we go out of bounds, switch direction and move to the next column pair
            if row < 0 or row >= size:
                row -= direction  # Step back to stay in bounds
                direction *= -1  # Reverse direction
                col -= 2  # Move to the next column pair
                break

    return matrix

def apply_mask(matrix):
    size = len(matrix)

    for i in range(size):
        for j in range(size):
            # Skip fixed patterns (where matrix cell is None or reserved)
            current = matrix[i][j]
            if current == 2 or current == 3:
                continue

            # Apply Mask 0 condition: (i + j) % 2 == 0
            if i % 2 == 0:
                matrix[i][j] = 1 if matrix[i][j] == 0 else 0  # Flip module value

    return matrix


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
            elif matrix[i][j] == 2:  # Finder patterns, timing patterns, etc.
                #color = (240, 50, 50)  # Red
                color = (255, 255, 255)  # White
            elif matrix[i][j] == 3:  # Alignment patterns
                #color = (50, 50, 240)  # Blue
                color = (0, 0, 0)  # Black
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
print("CCI:", cci)
encoded_str = str_to_bin(qr_string)

terminator = "0000"

total = mi + cci + encoded_str + terminator

pb = pad_bytes(total)

total = total + pb

# FOR 3-L: Total Codewords Num = 440
print("TOTAL:", total)
print("TOTAL LEN:", len(total))

hex_total = hex(int(total, 2))[2:]
print("HEX TOTAL:", hex_total)

dec_total = hex_to_dec_list(hex_total)
print("DEC TOTAL:", dec_total)

## -- ##

total_codewords = 55

result = add_error_correction(dec_total, total_codewords)

#print("RESULT:", result)
#print("RESULT LEN:", len(result))

test_result = "010000011110011010000111010001110100011100000111001100111010001011110010111101101101011011110111010101101110011101000110000101101001011011100110110001101001011011110110111001101101011011110111011001101001011001010111001100101110011000110110111101101101000011101100000100011110110000010001111011000001000111101100000100011110110000010001111011000001000111101100000100011110110000010001111011000001000111101100000100011110110000010001111011000010011111101010100001001001101000010011100011001101110011011100110100001010000011100001000111110110000100101111100111010000000"

#print("REAL RESULT:", test_result)
#print("REAL RESULT LEN:", len(test_result))

new_result = total + "011011100110001010110111011011010101001011101010010101111001001000010010111101011011110011101100111111101001000110010001"

print("NEW RESULT:", new_result)
print("NEW RESULT LEN:", len(new_result))

aligned_matrix = create_alignment_matrix()
#print(np.array(aligned_matrix))

matrix = test_encode_matrix(aligned_matrix, new_result)
mask_matrix = apply_mask(matrix)

render_matrix_as_image(mask_matrix, box_size=20, file_name="qr_matrix.png")