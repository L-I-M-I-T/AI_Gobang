import pygame
import os
import time
import sys
import tkinter.messagebox
import random

# 参数设置
WIDTH = 720  #窗口宽度
HEIGHT = 720 #窗口高度
SIZE = 15 # 棋盘大小为15*15
SPACE = WIDTH // (SIZE+1)  #空格大小
FPS = 40  # 帧率

# 颜色设置
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# pygame初始化设定
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("人工智能-五子棋")
clock = pygame.time.Clock()

#设置背景
img_folder = "images"
bg_img = pygame.image.load(os.path.join(img_folder, "background.png"))
background = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
back_rect = background.get_rect()

#全局变量
win_flag = 0  # -1:white win;1:black win
color_flag = 1  # white
step = 0
matrix = [[0 for i in range(SIZE + 2)] for j in range(SIZE + 2)]  # 棋型矩阵
min_x, min_y, max_x, max_y = 0, 0, 0, 0  # 搜索范围
movements = []  # 记录移动步骤
game_over = True
running = True
start = 1

# 绘制网格线
def draw_background(surf):
    screen.blit(background, back_rect)
    
    #画棋盘的网格线
    rect_lines = [((SPACE, SPACE), (SPACE, HEIGHT - SPACE)),
                  ((SPACE, SPACE), (WIDTH - SPACE, SPACE)),
                  ((SPACE, HEIGHT - SPACE), (WIDTH - SPACE, HEIGHT - SPACE)),
                  ((WIDTH - SPACE, SPACE), (WIDTH - SPACE, HEIGHT - SPACE))]
    #画边框的四条线
    for line in rect_lines:
        pygame.draw.line(surf, BLACK, line[0], line[1], 2)
    #画里面的线
    for i in range(17):
        pygame.draw.line(surf, BLACK, (SPACE * (2 + i), SPACE),
                         (SPACE * (2 + i), HEIGHT - SPACE))
        pygame.draw.line(surf, BLACK,
                         (SPACE, SPACE * (2 + i)),
                         (HEIGHT - SPACE, SPACE * (2 + i)))
     #画棋盘上的黑色标记   
    circle_center = [(SPACE * 4, SPACE * 4),
                     (SPACE * 8, SPACE * 4),
                     (SPACE * 12, SPACE * 4),
                     (SPACE * 4, SPACE * 8),
                     (SPACE * 8, SPACE * 8),
                     (SPACE * 12, SPACE * 8),
                     (SPACE * 4, SPACE * 12),
                     (SPACE * 8, SPACE * 12),
                     (SPACE * 12, SPACE * 12)]
    
    for circle in circle_center:
        pygame.draw.circle(surf, BLACK, circle, 6)

# 刷新棋盘已占有棋子的外切矩形范围
def xy_range(x, y):
    global min_x, min_y, max_x, max_y
    if step == 0:
        min_x, min_y, max_x, max_y = x, y, x, y
    else:
        if x < min_x:
            min_x = x
        elif x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        elif y > max_y:
            max_y = y

# 棋型评估
shape_score = {
    (0, 1, 0): 5,                 # 单子
    (0, 1, 1, -1): 10,            # 死2
    (-1, 1, 1, 0): 10,            # 死2
    (0, 1, 1, 0): 20,             # 活2
    (-1, 1, 1, 1, 0): 20,         # 死3
    (0, 1, 1, 1, -1): 20,         # 死3
    (0, 1, 1, 1, 0): 45,          # 活3
    (-1, 1, 1, 1, 1, 0): 60,      # 死4
    (0, 1, 1, 1, 1, -1): 60,      # 死4
    (0, 1, 1, 1, 1, 0): 120,      # 活4
    (0, 1, 1, 1, 1, 1, 0): 300,   # 成5
    (0, 1, 1, 1, 1, 1, -1): 300,
    (-1, 1, 1, 1, 1, 1, 0): 300,
    (-1, 1, 1, 1, 1, 1, -1): 300,
    (-1, 1, 1, 1, 1, 1, 1, -1): 300,
    (-1, 1, 1, 1, 1, 1, 1, 1, -1): 300
}

# 评估一个节点分值AI为正数 玩家为负数(调用的时候确定符号)
def evaluate(list_h, list_v, list_s, list_b):
    score_h = shape_score.get(tuple(list_h), 0)
    score_v = shape_score.get(tuple(list_v), 0)
    score_s = shape_score.get(tuple(list_s), 0)
    score_b = shape_score.get(tuple(list_b), 0)
    rank = [score_h, score_v, score_s, score_b]
    rank.sort()
    rank.reverse()
    #加入随即成分使得AI不会被同一方式连续打败
    #即使局面相同，节点的估分也不一定相同
    prob=random.randint(1,100)#prob=(0,100)
    if prob<80:    #0.8的概率选择此种估分
        score = rank[0] + rank[1]  # 把最大的两个分值相加作为总分值
    elif prob<95:  #0.15的概率选择此种估分
        score = rank[0] + rank[1]+rank[2]
    else:          #0.05的概率选择此种估分
        score = rank[0] + rank[1]+rank[2]+rank[3]
    return score

# 获得该结点在水平、竖直、左斜、右斜方向上构成的同色的棋子
def get_list(mx, my, color):
    global matrix

    #水平方向上
    list1 = []
    tx, ty = mx, my
    while matrix[tx][ty] == color:
        list1.append(1)  # 1表示是己方棋子，-1是敌方棋子
        tx = tx + 1
        ty = ty
    if matrix[tx][ty] == -color or tx == 0 or ty == 0 or tx > SIZE or ty > SIZE:
        list1.append(-1)
    else:
        list1.append(0) 
    list1.pop(0)  # 删除自己 防止在合并的时候重复计算
    list2 = []
    tx = mx
    ty = my
    while matrix[tx][ty] == color:
        list2.append(1)
        tx = tx - 1
        ty = ty
    if matrix[tx][ty] == -color or tx == 0 or ty == 0 or tx > SIZE or ty > SIZE:
        list2.append(-1)
    else:
        list2.append(0)
    list2.reverse()
    list_h = list2 + list1

    #竖直方向
    list1 = []
    tx = mx
    ty = my
    while matrix[tx][ty] == color:
        list1.append(1)
        tx = tx
        ty = ty + 1
    if matrix[tx][ty] == -color or tx == 0 or ty == 0 or tx > SIZE or ty > SIZE:
        list1.append(-1)
    else:
        list1.append(0)
    list1.pop(0)
    list2 = []
    tx = mx
    ty = my
    while matrix[tx][ty] == color:
        list2.append(1)
        tx = tx
        ty = ty - 1
    if matrix[tx][ty] == -color or tx == 0 or ty == 0 or tx > SIZE or ty > SIZE:
        list2.append(-1)
    else:
        list2.append(0)
    list2.reverse()
    list_v = list2 + list1

    #右斜
    list1 = []
    tx = mx
    ty = my
    while matrix[tx][ty] == color:
        list1.append(1)
        tx = tx + 1
        ty = ty + 1
    if matrix[tx][ty] == -color or tx == 0 or ty == 0 or tx > SIZE or ty > SIZE:
        list1.append(-1)
    else:
        list1.append(0)
    list1.pop(0)
    list2 = []
    tx = mx
    ty = my
    while matrix[tx][ty] == color:
        list2.append(1)
        tx = tx - 1
        ty = ty - 1
    if matrix[tx][ty] == -color or tx == 0 or ty == 0 or tx > SIZE or ty > SIZE:
        list2.append(-1)
    else:
        list2.append(0)
    list2.reverse()
    list_s = list2 + list1

    #左斜
    list1 = []
    tx = mx
    ty = my
    while matrix[tx][ty] == color:
        list1.append(1)
        tx = tx + 1
        ty = ty - 1
    if matrix[tx][ty] == -color or tx == 0 or ty == 0 or tx > SIZE or ty > SIZE:
        list1.append(-1)
    else:
        list1.append(0)
    list1.pop(0)
    list2 = []
    tx = mx
    ty = my
    while matrix[tx][ty] == color:
        list2.append(1)
        tx = tx - 1
        ty = ty + 1
    if matrix[tx][ty] == -color or tx == 0 or ty == 0 or tx > SIZE or ty > SIZE:
        list2.append(-1)
    else:
        list2.append(0)
    list2.reverse()
    list_b = list2 + list1

    return [list_h, list_v, list_s, list_b]

# 判断搜索范围是否超出边界，返回合法的搜索范围
def range_legal(_min_x, _min_y, _max_x, _max_y):
    delta = 1
    if _min_x - delta < 1:
        min_tx = 1
    else:
        min_tx = _min_x - delta

    if _min_y - delta < 1:
        min_ty = 1
    else:
        min_ty = _min_y - delta

    if _max_x + delta > SIZE:
        max_tx = SIZE
    else:
        max_tx = _max_x + delta

    if _max_y + delta > SIZE:
        max_ty = SIZE
    else:
        max_ty = _max_y + delta
    return [min_tx, min_ty, max_tx, max_ty]

# alpha-beta剪枝搜索
def ai_go():
    global min_x, max_x, min_y, max_y, color_flag, matrix
    time_start = time.time()
    evaluate_matrix = [[0 for i in range(SIZE + 2)] for j in range(SIZE + 2)]  # 结点估值矩阵
    if step != 0:
        if step == 1:
            #第一步下的位置
            if matrix[(SIZE + 1) // 2][(SIZE + 1) // 2] == 0:
                rx, ry = (SIZE + 1) // 2,(SIZE + 1) // 2
            else:
                if matrix[(SIZE + 1) // 2][(SIZE + 1) // 2] != 0 and matrix[(SIZE + 1) // 2 + 1][(SIZE + 1) // 2 + 1] == 0:
                    rx, ry = (SIZE + 1) // 2 + 1,(SIZE + 1) // 2 + 1
        else:        
            min_tx1, min_ty1, max_tx1, max_ty1 = range_legal(min_x, min_y, max_x, max_y)
            evaluate_matrix = [[0 for i in range(SIZE + 2)] for j in range(SIZE + 2)]  # 第一层的估值矩阵
            Max = -100000
            rx, ry = 0, 0

            for i in range(min_tx1, max_tx1 + 1):
                for j in range(min_ty1, max_ty1 + 1):
                    cut_flag = 0  # 剪枝标记
                    evaluate_matrix2 = [[0 for i in range(SIZE + 2)] for j in range(SIZE + 2)]

                    if matrix[i][j] == 0:
                        matrix[i][j] = color_flag
                        min_tx2, min_ty2, max_tx2, max_ty2 = range_legal(min_tx1, min_ty1, max_tx1, max_ty1)
                        [list_h, list_v, list_s, list_b] = get_list(i, j, color_flag)
                        eva1 = evaluate(list_h, list_v, list_s, list_b)

                        for ii in range(min_tx2, max_tx2 + 1):
                            for jj in range(min_ty2, max_ty2 + 1):

                                if matrix[ii][jj] == 0:
                                    matrix[ii][jj] = -color_flag                                  
                                    [list_h, list_v, list_s, list_b] = get_list(ii, jj, -color_flag)
                                    eva2 = -evaluate(list_h, list_v, list_s, list_b)    
                                                   
                                    evaluate_matrix2[ii][jj] = eva2 + eva1
                                    matrix[ii][jj] = 0
                                    # 剪枝
                                    if evaluate_matrix2[ii][jj] < Max:
                                        evaluate_matrix[i][j] = evaluate_matrix2[ii][jj]
                                        cut_flag = 1
                                        break
                            if cut_flag:
                                break

                        if cut_flag == 0:
                            Min = 100000
                            for ii in range(min_tx2, max_tx2 + 1):
                                for jj in range(min_ty2, max_ty2 + 1):
                                        if evaluate_matrix2[ii][jj] < Min and matrix[ii][jj] == 0:
                                            Min = evaluate_matrix2[ii][jj]

                            evaluate_matrix[i][j] = Min

                            if Max < Min:
                                Max = Min
                                rx, ry = i, j

                        matrix[i][j] = 0

        time_end = time.time()
        print("Time cost:", round(time_end - time_start, 4), "s")
        add_chess(rx, ry, color_flag)

# 添加棋子
def add_chess(x, y, color):
    global step, matrix
    step = step + 1
    movements.append((x, y, color, step))
    matrix[x][y] = color
    xy_range(x, y)
    game_judge()

# 悔棋
def back_chess():
    global step, matrix
    i=0
    while i!=2 and len(movements):
        step = step - 1
        x = movements[-1][0]
        y = movements[-1][1]
        del movements[-1]
        matrix[x][y] = 0 
        i=i+1

# 绘制文本
def draw_text(surf, text, size, x, y, color):
    font = pygame.font.SysFont("arial", size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    surf.blit(text_surface, text_rect)

# 绘制棋子
def draw_movements(surf):
    for move in movements:
        if move[2] == color_flag:
                pygame.draw.circle(surf, WHITE, (move[0] * SPACE, move[1] * SPACE), 16)
                draw_text(surf, str(move[3]), 10, move[0] * SPACE, move[1] * SPACE, BLACK)             
        else:
                pygame.draw.circle(surf, BLACK, (move[0] * SPACE, move[1] * SPACE), 16)
                draw_text(surf, str(move[3]), 10, move[0] * SPACE, move[1] * SPACE, WHITE)

# 玩家行棋
def player_go(pos):
    x = round(pos[0] / SPACE)
    y = round(pos[1] / SPACE)
    if 1 <= x <= SIZE and 1 <= y <= SIZE and matrix[x][y] == 0:
        add_chess(x, y, -color_flag)
        return True

# 判断游戏是否结束
def game_judge():
    global win_flag, game_over, start
    x = movements[-1][0]
    y = movements[-1][1]
    color = movements[-1][2]
    [list_h, list_v, list_s, list_b] = get_list(x, y, color)
    if sum(list_h[1:-1]) == 5 or sum(list_v[1:-1]) == 5 or sum(list_s[1:-1]) == 5 or sum(list_b[1:-1]) == 5:
        win_flag = color
        game_over = True
        start = 1

# 开始界面显示
def init_UI(surf):
    global win_flag, movements, step, matrix, min_x, min_y, max_x, max_y, game_over, start
    if start == 1:
        if win_flag != 0:
            root = tkinter.Tk()
            root.withdraw()
            if win_flag == 1:
                tkinter.messagebox.showinfo("游戏结束","你输了!")
            else:
                tkinter.messagebox.showinfo("游戏结束","你赢了!")
        else:
            screen.blit(background, back_rect)
        draw_text(surf, "Press Enter to Start", 22, WIDTH // 2, 500, BLUE)
        
    pygame.display.flip()
    win_flag = 0
    movements = []
    step = 0
    matrix = [[0 for i in range(SIZE + 2)] for j in range(SIZE + 2)]
    min_x, min_y, max_x, max_y = 0, 0, 0, 0
    game_over = False
    waiting = True
    while waiting and start:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    ai_go()
                    waiting = False
    start = 0

# 主循环
while running:
    if game_over:
        init_UI(screen)
    clock.tick(FPS)
    if step % 2 == 1:
        ai_go()
    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                player_go(event.pos)
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_over=True
                elif event.key == pygame.K_w:
                    back_chess()
                elif event.key == pygame.K_g:
                    running=False
                    
    draw_background(screen)
    draw_movements(screen)
    draw_text(screen, "r=restart w=withdraw g=game over", 25, WIDTH // 2, 20, BLUE)
    pygame.display.flip()

pygame.quit()
sys.exit()

