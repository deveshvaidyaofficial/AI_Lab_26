import simpleguitk as simplegui

HEIGHT = 400
WIDTH = 500
NODE_SPACE_ALLOWANCE = 20
EDGE_COLOR = "Yellow"
EDGE_SIZE = 2
NODE_LABEL_COLOR = "White"
NODE_COLOR = "Red"
NODE_MARK_COLOR = "Green"

start = 0
goal = 0
placeNodes = True
setNodesRelation = False
draw_relations = False
draw_mark_relations =  False
setGoal = False
setStart = False
displayResult = False
lock_nodes = False
nodes = []

pos1 = [0,0]
pos2 = [0,0]
pos_lock = False
indx = 0



class Point:
    def __init__(self,pos,node_colour,node_mark_colour):
        self.pos = pos
        self.children = []
        self.radius = 5
        self.colour = node_colour
        self.mark_colour = node_mark_colour
        self.index = 0
        self.is_mark = False
        self.label = -1
    def draw(self,canvas):
        if self.is_mark == False:
            canvas.draw_circle(self.pos, self.radius, 6, self.colour)
        else:
            canvas.draw_circle(self.pos, self.radius, 6, self.mark_colour)



def mouseclick(pos):
    global pos1, pos2, pos_lock, indx, draw_relations, draw_mark_relations, nodes, indx_mark_color
    global letter_label_default, letter_pos
    
    allow_place_node = True
    
    if placeNodes == True:
        if nodes: 
            for p, location in enumerate(nodes):
                if ((pos[0] >= (nodes[p].pos[0]-NODE_SPACE_ALLOWANCE) and pos[0] <= (nodes[p].pos[0]+NODE_SPACE_ALLOWANCE)) and
                    (pos[1] >= (nodes[p].pos[1]-NODE_SPACE_ALLOWANCE) and pos[1] <= (nodes[p].pos[1]+NODE_SPACE_ALLOWANCE))):
                    print( "Warning: Cannot create node on top of another node!" )  
                    allow_place_node = False
                    break
        
            if allow_place_node == True:
                nodes.append(Point(pos, NODE_COLOR, NODE_MARK_COLOR))
                nodes[-1].label = len(nodes) - 1
     
        else:  
            nodes.append(Point(pos,NODE_COLOR,NODE_MARK_COLOR))
            nodes[-1].label = chr(ord(letter_label_default) + letter_pos)
            letter_pos += 1
    
  
    if setNodesRelation == True:
        
        for i, position in enumerate(nodes):
            if ((pos[0] >= (nodes[i].pos[0]-NODE_SPACE_ALLOWANCE) and pos[0] <= (nodes[i].pos[0]+NODE_SPACE_ALLOWANCE)) and
                (pos[1] >= (nodes[i].pos[1]-NODE_SPACE_ALLOWANCE) and pos[1] <= (nodes[i].pos[1]+NODE_SPACE_ALLOWANCE))):
                if pos_lock == False:
                    pos1[0] = pos[0]
                    pos1[1] = pos[1]
                    
                    indx = i
                    indx_mark_color = i
                    pos_lock = True
                    draw_mark_relations = True
                    break

                else:
                    if i != indx:
                        pos2[0] = pos[0]
                        pos2[1] = pos[1]
                        nodes[indx].children.append(i)
                        nodes[i].children.append(indx)
                        
                        pos_lock = False
                        draw_relations = True
                        draw_mark_relations = False
                        break
                    else:
                        print( "Warning: Recursion or self loop is not allowed." ) 


def button_refresh_new_relation():
    global pos_lock, pos1, pos2, nodes, draw_relations, draw_mark_relations
    
    if lock_nodes == False and setNodesRelation == True:
        pos_lock = False
        draw_mark_relations = False
        draw_relations = False
        pos1[0] = 0
        pos1[1] = 0
        pos2[0] = 0
        pos2[1] = 0

        for i, child in enumerate(nodes):
            del nodes[i].children[:]
    else:
        print( "Warning: This action is not allowed." )


def button_lock_nodes():
    global placeNodes, setNodesRelation, current_node_letters_up, nodes, current_node_letters_low
    
    if placeNodes == True and setNodesRelation == False and setStart == False and setGoal == False:
        placeNodes = False
        setNodesRelation = True
        
def button_lock_graph():
    global placeNodes, setNodesRelation, nodes, lock_nodes
    
    if setNodesRelation is True:
        placeNodes = False
        setNodesRelation = False
        lock_nodes = True

        for d, dot in enumerate(nodes):
            nodes[d].index = d
            print("Node", d, ":", nodes[d].label)
                        
            nodes[d].children.sort()

        print( "Graph is now set!" )
    else:
        print( "Warning: This action is not allowed." )

def input_start_handler(start_string):
    global start, setStart

    setStart = False

    if start_string.isdigit():
        temp = int(start_string)

        if 0 <= temp < len(nodes):
            start = temp
            setStart = True
            print("Start:", start)
        else:
            print("Invalid start node.")
    else:
        print("Enter a valid node number.")

def input_goal_handler(goal_string):
    global goal, setGoal

    setGoal = False

    if goal_string.isdigit():
        temp = int(goal_string)

        if 0 <= temp < len(nodes):
            goal = temp
            setGoal = True
            print("Goal:", goal)
        else:
            print("Invalid goal node.")
    else:
        print("Enter a valid node number.")
        
def button_breadth_first_search():
    global nodes, displayResult, result_string, queue_string, pointer_string
    displayResult = False
    pointer_string = ""

    for d, marking_obj in enumerate(nodes):
        nodes[d].is_mark = False

    in_queue_result = False

    if placeNodes == False and setNodesRelation == False and setStart == True and setGoal == True:
        print( " " )
        print( "BFS starts here:" )
        
        try:
            queue
        except:
            queue = []
        else:
            del queue[:]

        queue.append(nodes[start])
        queue[0].is_mark = True
        
        try:
            result
        except:
            result = []
        else:
            del result[:]
        
        while queue:
            pointer = queue[0]
            queue.pop(0)
            
            pointer.is_mark = True
            print( " " )
            print( "Pointer:", pointer.label )
            
            if pointer.index == goal:
                pointer_string =  "Pointer: " + pointer.label
                result_string = "Result: "
                queue_string = "Queue: "
                
                for obj in result:
                    result_string += str(obj.label)
                    result_string += " "
                for objt in queue:
                    queue_string += str(objt.label)
                    queue_string += " "
                
                displayResult = True
                print( "SUCCESS!" )
                break
            else:
                result.append(pointer)

                for neighbor in pointer.children:
                    in_queue_result = False
                    for i in queue:
                        if neighbor == i.index:
                            in_queue_result = True
                            
                    for j in result:
                        if neighbor == j.index:
                            in_queue_result = True

                    if in_queue_result == False:
                        for objct in nodes:
                            if objct.index == neighbor:
                                queue.append(nodes[objct.index])
            result_string = "Result: "
            queue_string = "Queue: "
            for obj in result:
                result_string += str(obj.label)
                result_string += " "
            print( result_string )

            for objt in queue:
                queue_string += str(objt.label)
                queue_string += " "
            print( queue_string )

def button_depth_first_search():
    global nodes, displayResult, result_string, queue_string, pointer_string
    displayResult = False
    pointer_string = ""

    for d, marking_obj in enumerate(nodes):
        nodes[d].is_mark = False

    in_queue_result = False

    if placeNodes == False and setNodesRelation == False and setStart == True and setGoal == True:
        print( " " )
        print( "DFS starts here:" )
        
        try:
            queue
        except:
            queue = []
        else:
            del queue[:]
        
        queue.append(nodes[start])
        queue[0].is_mark = True
        try:
            result
        except:
            result = []
        else:
            del result[:]


        try:
            temp_list
        except:
            temp_list = []
        else:
            del temp_list[:]
         

        while queue:
            pointer = queue[0]
            queue.pop(0)
            pointer.is_mark = True
            print( " " )
            print( "Pointer:", pointer.label )

            if pointer.index == goal:
                pointer_string =  "Pointer: " + pointer.label
                result_string = "Result: "
                queue_string = "Queue: "
                
                for obj in result:
                    result_string += str(obj.label)
                    result_string += " "
                for objt in queue:
                    queue_string += str(objt.label)
                    queue_string += " "
                
                displayResult = True
                print( "SUCCESS!" )
                break
            else:
                result.append(pointer)
                del temp_list[:]
                
                for neighbor in pointer.children:
                    in_queue_result = False

                    for i in queue:
                        if neighbor == i.index:
                            in_queue_result = True
                            
                    for j in result:
                        if neighbor == j.index:
                            in_queue_result = True

                    if in_queue_result == False:
                        for obj in nodes:
                            if obj.index == neighbor:
                                temp_list.append(nodes[obj.index])
                
                if temp_list:      
                    queue[0:0] = temp_list

            result_string = "Result: "
            queue_string = "Queue: "
            for obj in result:
                result_string += str(obj.label)
                result_string += " "
            print( result_string )

            for objt in queue:
                queue_string += str(objt.label)
                queue_string += " "
            print( queue_string )


def draw_handler(canvas):
    global result_string, queue_string, pointer_string
    global placeNodes, setNodesRelation, setStart, setGoal, pos1
    
    if draw_mark_relations == True and setNodesRelation == True:
        canvas.draw_circle(nodes[indx_mark_color].pos, 15, 3, "Yellow", "Black")

    if nodes: 
        for i, vertex in enumerate(nodes):
            nodes[i].draw(canvas)
            canvas.draw_text(nodes[i].label, (nodes[i].pos[0]-30, nodes[i].pos[1]), 20, NODE_LABEL_COLOR)

    if draw_relations == True:
        for n, point in enumerate(nodes):
            if nodes[n].children: 
                for child in nodes[n].children:
                    canvas.draw_line(nodes[n].pos, nodes[child].pos, EDGE_SIZE, EDGE_COLOR)

    if displayResult == True:
        canvas.draw_text(pointer_string, (30, 345), 15, NODE_LABEL_COLOR)
        canvas.draw_text(result_string, (30, 370), 15, NODE_LABEL_COLOR)
        canvas.draw_text(queue_string, (30, 395), 15, NODE_LABEL_COLOR)


frame = simplegui.create_frame("Graph Node Search with BFS and DFS",WIDTH,HEIGHT)

frame.set_mouseclick_handler(mouseclick)
frame.set_draw_handler(draw_handler)

button1 = frame.add_button('Lock in the nodes', button_lock_nodes)
label1 = frame.add_label(' ')

button2 = frame.add_button('Lock in the graph', button_lock_graph)
label2 = frame.add_label(' ')

button3 = frame.add_button('Reset edge drawing', button_refresh_new_relation)
label3 = frame.add_label(' ')

input_start = frame.add_input('Set start', input_start_handler, 50)
label4 = frame.add_label(' ')

input_goal = frame.add_input('Set goal', input_goal_handler, 50)
label5 = frame.add_label(' ')

button4 = frame.add_button('Find BFS', button_breadth_first_search)
button5 = frame.add_button('Find DFS', button_depth_first_search)

frame.start()