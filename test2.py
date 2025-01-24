from random import *
from tkinter import *
from time import *
from PIL import Image,ImageTk
from math import *
'''
General logic behind how the game works:

Game will take place in a 10x10 grid.

Each square in this grid will be another smaller 10x10 grid, that you can traverse
Player won't notice grid, only make this syste to make it easier to make.

At any given moment, just have 9 of this big squares loaded. The center, and 4 adjacent sides
Then once we scroll over to another square, we delete the olds one from screen, and then generate new ones.

Each part of the 10x10 grid will be the size of the current screen. (500x500)
Each part of grid will have 100 50x50 squares

Also when drawing enemies, make sure you draw a background behind them, as they will be moving.
To make updating the screen easier with scrolling, group by tags. This lets us move many objects with one command
'''


class objectManager():
    '''
    This object is used to manage all the smaller objects within the 10x10 grid.
    This lets me update the screen much much easier.
    '''
    def __init__(self,canvas):
        self.canvas=canvas#Canvas
        self.groups={}#Groups that we keep track of
        self.objectQuery={}#Where we can query object id's to figure what the object is. Key is the group name. Within it, is another dictionary where the key is object id and the value objectType

    def createGroup(self,groupName):
        '''
        This method creates a group called groupName
        '''
        self.groups[groupName]=[]
        self.objectQuery[groupName]={}

    def add(self,groupName,objId,objType):
        '''
        Adds an object to a group.
        '''
        self.groups[groupName].append(objId)
        self.canvas.addtag_withtag(groupName,objId)
        self.objectQuery[groupName][objId]=objType

    def moveGroup(self,groupName,dx,dy):
        '''
        Moves the group by a specified amount.
        '''
        self.canvas.move(groupName,dx,dy)

    def deleteGroup(self,groupName):
        '''
        Deletes a group
        '''
        self.canvas.delete(groupName)
        del self.groups[groupName]
        del self.objectQuery[groupName]

    def editObject(self,groupName,objectId,newObjectId,newObjectType):
        '''
        Updates the group with objectId with newObjectId
        And updates objecType of objectId with with new id and type.
        '''
        if objectId in self.groups[groupName]:
            self.groups[groupName].remove(objectId)#Remove old object id

        self.groups[groupName].append(newObjectId)
        self.canvas.addtag_withtag(groupName,newObjectId)#Update the tag with this new object


        if objectId in self.objectQuery[groupName]:
            del self.objectQuery[groupName][objectId]#Removes the old dictionary entry, since this object has changed
        
        self.objectQuery[groupName][newObjectId]=newObjectType
        
    
    def getObject(self,groupName,objId):
        '''
        Gets object type from groupName and object id
        '''
        if objId in self.objectQuery[groupName]:
            return self.objectQuery[groupName][objId]
    
        

class Grid():
    '''
    This objects is for the entire game map. This is where the levels are generated and drawn
    '''
    def __init__(self,n):
        #Coordinates are top down. So top left will be (0,0)

        self.n=n#Size of grid
        self.grid={}#Key is row,col, and value is the 2d array of the grid
        self.gridObjets={}#Key is row,col and value is a list of all tkinter objects for that location. 
        self.imageCache={}#Key is image path, newWidth,newHeight and value is the image object itself
        self.enemyImages=set([])#To make sure images aren't deleted
        self.chestLocations={}#key is location, value is another dictionary. In that dictionary key is id and value is location
        
        self.swingSpeedUpgrade=None#Id of the swingSpeed upgrade
        self.knockbackUpgrade=None#Id of the knockback upgrade
        self.ra=None#Id of the eye of ra
        self.potion=None#Id of potion
        
        
        #Special locations: 
        self.blackMarketCoords=(randint(4,5),randint(4,5))
        self.bossCoords=(choice([1,2,7,8]),choice([1,2,7,8]))
    
    def reset(self):
        '''
        Resets all the values
        '''
        self.grid={}#Key is row,col, and value is the 2d array of the grid
        self.gridObjets={}#Key is row,col and value is a list of all tkinter objects for that location. 
        self.imageCache={}#Key is image path, newWidth,newHeight and value is the image object itself
        self.enemyImages=set([])#Key is location,
        self.chestLocations={}#key is location, value is another dictionary. In that dictionary key is id and value is location
        
        self.swingSpeedUpgrade=None#Id of the swingSpeed upgrade
        self.knockbackUpgrade=None#Id of the knockback upgrade
        self.ra=None#Id of the eye of ra
        self.potion=None#Id of potion
        
        
        #Special locations: 
        self.blackMarketCoords=(randint(4,5),randint(4,5))
        self.bossCoords=(choice([1,2,7,8]),choice([1,2,7,8]))
        
    def resizeImage(self, imgPath, newWidth, newHeight):
        '''
        This method resizes an image to specified dimenions
        '''
        if (imgPath,newWidth,newHeight) in self.imageCache:
            return self.imageCache[(imgPath,newWidth,newHeight)]

        img=Image.open(imgPath).resize((newWidth,newHeight))
        newPhotoImage=ImageTk.PhotoImage(img)
        self.imageCache[(imgPath, newWidth, newHeight)]=newPhotoImage#If I don't do this, images will get deleted.
        return newPhotoImage 

    def generateLevel(self,row,col):
        '''
        Generates the level at (row,col)
        '''

        def makeStructure(structureType,numTries,level):
            '''
            This method will attempt to place a structure in the level
            '''
            #Don't try points systematically, since that means we will level up with structures at the start
            for i in range(numTries):
                x,y=randint(0, self.n-1),randint(0,self.n-1)
                if safeZoneX[0]<=x<=safeZoneX[1] and safeZoneY[0]<=y<=safeZoneY[1]:
                    continue

                if structureType=="CC" and x>0 and y>0:
                    # Cacti clump
                    if level[x][y]==0 and level[x][y-1]==0 and level[x-1][y]==0:
                        level[x][y]=1
                        level[x][y-1]=1
                        level[x-1][y]=1
                        return level
                elif structureType in {"CE", "PC", "EH"} and x < self.n-1 and y>0 and y < self.n-1:
                    #Chest-enemy, Pyramid-chest, or Enemy horde structures
                    if level[x][y]==0 and level[x][y+1]==0 and level[x][y-1]==0 and level[x+1][y]==0 and level[x+1][y-1]==0 and level[x+1][y+1]==0:
                        #update level
                        level[x][y]=4
                        level[x][y+1]=6 if structureType!="PC" else 3
                        level[x][y-1]=6 if structureType!="PC" else 3
                        level[x+1][y]=6 if structureType!="PC" else 3
                        level[x+1][y-1]=6 if structureType!="PC" else 3
                        level[x+1][y+1]=6 if structureType!="PC" else 3
                        return level
            return level
            


        safeZoneRadius=2#Number of tiles around spawn location to keep empty
        spawnX,spawnY=4,4#Spawn location
        safeZoneX=(max(0,spawnX-safeZoneRadius), min(self.n-1,spawnX+safeZoneRadius))
        safeZoneY=(max(0,spawnY-safeZoneRadius), min(self.n-1, spawnY+safeZoneRadius))

        if (row,col)==self.blackMarketCoords:#Set level no matter what
            level=[
                [1,1,0,0,0,0,0,0,1,1],
                [1,0,0,0,0,0,0,0,0,1],
                [0,0,12,12,12,12,12,12,0,0],
                [0,0,0,9,0,0,10,0,0,0],
                [0,0,12,1,0,0,1,12,0,0],
                [0,0,12,1,0,0,1,12,0,0],
                [0,0,0,11,0,0,8,0,0,0],
                [0,0,12,12,12,12,12,12,0,0],
                [1,0,0,0,0,0,0,0,0,1],
                [1,1,0,0,0,0,0,0,1,1],
                ]
            self.grid[(row,col)]=level
            return
        
        if (row, col)==self.bossCoords:
            #Special level, should just be empty
            level=[[0]*self.n for i in range(self.n)]
            self.grid[(row,col)]=level
            return
        
        
        #Normal level
        level=[[0]*self.n for i in range(self.n)]

        numStructures=randint(5,9)#Number of structures
        for i in range(numStructures):
            randNum=randint(1, 100)
            if randNum<=30:
                level=makeStructure("CC",100,level)
            elif randNum<=60:
                level=makeStructure("CE",100,level)
            elif randNum <= 80:
                level=makeStructure("PC",100,level)
            else:
                level=makeStructure("EH",100,level)
        #Store the generated level
        self.grid[(row,col)]=level


    def drawLevel(self,row,col,enemyManager,manager,xOffset=0,yOffset=0):
        '''
        This method draws (row,col) level. Updates the object and enemy manager. Offsets are initally 0
        These offsets are to draw things that are offscreen
        '''
        def drawObject(value):
            '''
            This function returns the image object for each objectType
            '''
            #0 will be nothing (sand)
            #1 will be a cactus
            #2 will be a tree
            #3 will be a pyramid
            #4 will be a chest
            #5 will be opened chest
            #6 will be a enemy
            #7 will be water
            #8 will be eye of ra
            #9 will be upgrade1 (Swing speed) 
            #10 will be upgrade2 (Knockback)
            #11 will be potion to increase health
            #12 will be brick
            if value==0:
                return self.resizeImage("sand.png",50,50)
            elif value==1:
                return self.resizeImage("cactus.png",50,50)
            elif value==3:
                return self.resizeImage("pyramid.png",50,50)
            elif value==4:
                return self.resizeImage("closedChest.png",50,50)
            elif value==5:
                return self.resizeImage("openedChest.png",50,50)
            elif value==6:
                return self.resizeImage("badGuy.png",50,50)
            elif value==8:
                return self.resizeImage("eyeOfRa.png",50,50)
            elif value==9:
                return self.resizeImage("swingSpeed.png",50,50)
            elif value==10:
                return self.resizeImage("knockback.png",50,50)
            elif value==11:
                return self.resizeImage("potion.png",50,50)
            elif value==12:
                return self.resizeImage("brick.png",50,50)


        if (row,col) not in self.grid:
            #For debugging, shouldn't happen.
            raise Exception("Trying to draw level that wasn't generated")
        
        manager.createGroup((row,col))#Create group for these objects

        level=self.grid[(row,col)]

        if (row,col) not in self.chestLocations:
            self.chestLocations[(row,col)]={}


        for i in range(self.n):
            for j in range(self.n):
                objectType=level[i][j]
                if objectType==6:

                    backDrop=drawObject(0)#Sand
                    temp=screen.create_image(25+j*50+xOffset,25+i*50+yOffset,image=backDrop)
                    manager.add((row,col),temp,objectType)

                    temp2=Image.open("badGuy.png").resize((40,40))#Bad guy
                    enemy=ImageTk.PhotoImage(temp2)

                    self.enemyImages.add(enemy)

                    temp=screen.create_image(j*50+xOffset,i*50+yOffset,image=enemy,anchor="nw")
                    manager.add((row,col),temp,6)
                    enemyManager.addEnemy(row,col,j*50,i*50,temp)


                else:
                    image=drawObject(objectType)
                    temp=screen.create_image(j*50+xOffset,i*50+yOffset,image=image,anchor="nw")#NEED THIS ANCHOR, draws based on top left corner.
                    manager.add((row,col),temp,objectType)

                    #Updates object id's and locations
                    if objectType==4:
                        self.chestLocations[(row,col)][temp]=(j,i)#Row and column
                    elif objectType==8:
                        self.ra=temp
                    elif objectType==9:
                        self.swingSpeedUpgrade=temp
                    elif objectType==10:
                        self.knockbackUpgrade=temp
                    elif objectType==11:
                        self.potion=temp
                    


    def drawSurrounding(self,row,col,enemyManager,manager):
        '''
        This method is only called at the start
        It draws the 8 squares around a center position (row,col)
        This will only work for the start, as we don't take into account player movement for the offsets
        '''
        #row, col is the center square.
        #We need to draw the surrounding ones.
        change=[(0,1),(1,0),(1,1),(0,-1),(-1,0),(-1,-1),(-1,1),(1,-1)]
        offsets=[(500,0),(0,500),(500,500),(-500,0),(0,-500),(-500,-500),(500,-500),(-500,500)]
        for i in range(len(change)):
            rChange,cChange=change[i]
            xOffset,yOffset=offsets[i]
            newRow,newCol=row+rChange,col+cChange
            if 0<=newRow<self.n and 0<=newCol<self.n:
                #In range
                if (newRow,newCol) not in self.grid:
                    #Haven't generated this level
                    self.generateLevel(newRow,newCol)
                #Now write code to draw the level, accounting for previous squares as well

                self.drawLevel(newRow,newCol,enemyManager,manager,xOffset,yOffset)

class Enemy():
    '''
    This object manages all the enemies. It keeps track of their location, their stats, e.t.c
    '''
    def __init__(self,canvas):
        self.enemies={}#Key is grid location, value is a list of dictionaries, with enemy attributes 
        self.canvas=canvas
        self.hits={}#Key is enemy id, value is number of times it has been hit
    
    def reset(self):
        '''
        This method resets everything
        '''
        self.enemies={}#Key is grid location, value is a list of dictionaries, with enemy attributes 
        self.hits={}

    def addEnemy(self,row,col,enemyX,enemyY,enemyId):
        '''
        Adds newly loaded enemy
        enemyX,enemyY should be for the top left of the enemy
        '''
        if (row,col) not in self.enemies:
            self.enemies[(row,col)]=[]

        self.enemies[(row,col)].append({

            "id":enemyId,
            "initalX":enemyX,#Relative to their row,col. So no offset calculated yet
            "initalY":enemyY,
            "curX":enemyX,
            "curY":enemyY,
            "dx":0,#Change in dx and dy, so we know how to knock them back
            "dy":0,
            "state":"idle"#Can be idle or active. Idle means not chasing, active means chasing
            
        })        


    def moveEnemys(self,row,col,playerLocation,speed):
        '''
        This method moves the enemys in your row,col towards you by a step
        towards you. Doesn't actually draw them. Just updates the position
        '''
        if (row,col) not in self.enemies:
            return#No enemies in this location


        playerX,playerY=playerLocation[0]-30,playerLocation[1]-30

        for i,enemyData in enumerate(self.enemies[(row,col)]):
            if enemyData["state"]=="active" and screen.coords(enemyData["id"])!=[]:

                
                x,y=screen.coords(enemyData["id"])#Need updated x,y after moving around, since it will be different
                enemyData["curX"]=x
                enemyData["curY"]=y

                dx=playerX-enemyData["curX"]+randint(10,20)#Add some randomness, so they don't all group up
                dy=playerY-enemyData["curY"]+randint(10,20)
                distance=sqrt(dx**2+dy**2)

                
                if distance!=0:
                    dx=(dx/distance)*speed#Enemy speed
                    dy=(dy/distance)*speed
                
                newX,newY=enemyData["curX"]+dx,enemyData["curY"]+dy

                #Update values
                self.enemies[(row,col)][i]["curX"]=newX
                self.enemies[(row,col)][i]["curY"]=newY
                self.enemies[(row,col)][i]["dx"]=dx
                self.enemies[(row,col)][i]["dy"]=dy
                

    def unloadEnemies(self,row,col):
        '''
        This method unloads the enemies in (row,col)
        This is used when I move out of the square that enemies that were chasing me in. Just delete them,
        no need to do anything more, since when I load it again, I will re-add them.
        '''
        if (row,col) in self.enemies:
            for i,enemyData in enumerate(self.enemies[(row,col)]):
                #Have to delete the enemy rather than move them back. 
                #Then delete all enemies in that location, since you will delete them all
                screen.delete(enemyData["id"])
            self.enemies[(row,col)]=[]
                    
               
               
    def loadEnemies(self,row,col):
        '''
        This method loads the enemies in (row,col)
        '''
        if (row,col) in self.enemies:
            for i,enemyData in enumerate(self.enemies[(row,col)]):
                enemyData["state"]="active"
                self.enemies[(row,col)][i]=enemyData



    def updateEnemy(self,row,col,arcId,playerId,knockback,swingActive):
        '''
        Updates enemies in the given square, checks for collisions, and handles damage and death.
        '''
        
        gold=0#Local variable to see gold change
        healthLost=0

        if (row,col) not in self.enemies:
            return (gold,healthLost)#No enemies in this location

        tempPlayerId=playerId#Keep track of old playerId, since we don't want player health to reduce a ton
        #Use this, since we have some invicibility frames

        counter=0#Number of i-frames

        enemiesToRemove=[]#What enemies we need to delete

        for enemyData in self.enemies[(row, col)]:
            if enemyData["state"]=="active":

                #Get enemy's current position
                ex,ey=enemyData["curX"],enemyData["curY"]

                #Check for collisions with the sword arc
                hitbox=screen.find_overlapping(ex,ey,ex+10,ey+10)
                
                if hitbox and arcId in hitbox and swingActive:#Makes sure hitbox isn't none
                    enemyId=enemyData["id"]
                    
                    

                    # Track hits for this enemy
                    if enemyId not in self.hits:
                        self.hits[enemyId]=1#First hit
                    else:
                        self.hits[enemyId]+=1


                    #Check if the enemy should be killed

                    if self.hits[enemyId]>=2:#Enemy dies after 2 hits
                        screen.delete(enemyData["id"])#Remove enemy from the screen
                        enemiesToRemove.append(enemyData)  
                        gold+=1

                    else:
                        #Apply knockback effect if not killed
                        enemyData["curX"]-=enemyData["dx"]*knockback
                        enemyData["curY"]-=enemyData["dy"]*knockback
                        
                        screen.coords(enemyData["id"],enemyData["curX"],enemyData["curY"])
                        screen.tag_raise(enemyData["id"])  
                else:
                    #Update enemy's position normally
                    screen.coords(enemyData["id"],enemyData["curX"],enemyData["curY"])
                    screen.tag_raise(enemyData["id"]) 
            
                #Check player collisions
                if playerId!=None:
                    if hitbox and playerId in hitbox:
                        playerId=None
                        healthLost+=1
                        counter+=1
                else:
                    counter+=1
                    if counter==20:#No more i-frames
                        playerId=tempPlayerId
            
            

        #Remove defeated enemies from the list
        for enemy in enemiesToRemove:
            self.enemies[(row, col)].remove(enemy)
            del self.hits[enemy["id"]]#Clean up the hit tracker

        return (gold,healthLost)#To update global variables
        
    
        
        
        


root=Tk()

screen=Canvas(root, width=500, height=500, background="black")
# seed(42)#Just for testing, can remove this for random generation

def initalizeValues():
    '''
    What each variable does:
    gameStart: Just a check to make sure you can't swing your sword in the intro screen
    grid: The Grid object we use
    manager: The objectManager object we use
    playerPos: The player position on the big 10x10 grid
    viewingLocation: How we check when we offically enter a new square. Is what we use to check what more we need to load
    playerSpriteLocation: The location of the player graphic. Mostly stays the same, except on the edges
    pressedKeys: A set containing what keys are pressed. Just used to prevent diagonal movement
    enemySpeed: The speed the enemies come towards you at
    gold: How much gold you have
    health: How much health you have
    startingHealth: The starting health you have. Need 2 variables, since of the different difficulties
    mouseX: The x position of the mouse
    mouseY: The y position of the mouse
    isSwordSwing: A chest to see if the sword is currently swining
    playerMovement: A variable similar to viewingLocation, except it starts at 0,0 and is used to calcualte offsets after we've moved to draw new levels
    enemyManager: The Enemy object to manage enemies
    curSwordId: The current id of the sword image object
    knockback: How much knockback to apply to enemies
    playerId: The id of the player sprite. Used for collisions with enemies
    swingSpeed: How fast you swing your sword, and how fast it moves
    upgradeBox,upgradeTitle,upgradeDesc,upgradePrice: All image objects that need to be deleted and redrawn when hovering over upgrades
    upgradeVisible: Check to see if the ugprade stuff is still visible
    currentUpgrade: What upgrade you're currently on
    potionPrice,knockbackPrice,swingSpeedPrice,raPrice: The price of each shop item
    hasRa: Check to see if player has the eye of Ra
    updatePlayerId: The id of scheduling a player update. Used to fix a bug, where speed increased after you restarted a game
    updateEnemeyId: Same as above, but for enemy updates
    arrowId: The id of the arrow image
    arrowImage: The image id of the regular arrow, so it doesn't get deleted
    rotatedArrow: The image id of the rotated arrow, so it doesn't get deleted
    '''
    global gameStart
    global grid,manager,playerPos,viewingLocation,playerSpriteLocation,pressedKeys,enemySpeed
    global gold,health,startHealth,mouseX,mouseY,isSwordSwing,playerMovement,enemyManager,curSwordId
    global knockback,playerId,swingSpeed
    global upgradeBox,upgradeTitle,upgradeDesc,upgradePrice,upgradeVisible,currentUpgrade
    global potionPrice,knockbackPrice,swingSpeedPrice,raPrice
    global hasRa,updatePlayerId,updateEnemyId,arrowId,arrowImage,rotatedArrow
    
    gameStart=False
    grid=Grid(10)#Game grid
    manager=objectManager(screen)#Object manager
    enemyManager=Enemy(screen)#Enemy manager
    

    playerPos=[4,4]#Player position. (row,col)
    viewingLocation=[250,250]#What we will use to check if player is another square. Whenever we move, update this.
    #viewingLocation[0] is x. viewingLocation[1] is y.
    playerMovement=[0,0]#Keep tracks of how the player moves, resets whenever needed. 
    playerSpriteLocation=[250,250]#Location of the player sprite

    enemySpeed=3

    pressedKeys=set([])#Keeps track of keys, to prevent diagonal movment
    gold=0
    health=100
    startHealth=health
    mouseX,mouseY=0,0
    isSwordSwing=False
    
    curSwordId=None
    
    knockback=10#knockback when you hit something
    swingSpeed=10
    playerId=None
    arrowImage=None
    rotatedArrow=None#So doesn't get delted
    arrowId=None

    upgradeBox,upgradeTitle,upgradeDesc,upgradePrice=None,None,None,None#The textbox and text for the shop
    upgradeVisible=False#If the upgrade text is visisble
    currentUpgrade=False

    potionPrice=50
    knockbackPrice=40
    swingSpeedPrice=40
    raPrice=300

    hasRa=False
    updatePlayerId=None
    updateEnemyId=None



def checkCollision(newX,newY):
    '''
    Check for collisions at new player position
    Check surrounding groups, since you have to be at 250,250 to be considered at a new level (makes sense when you think about level loading)
    '''
    global manager,health
    hitbox=screen.find_overlapping(newX-15, newY-15, newX+15, newY+15)
    # screen.create_rectangle(newX-10, newY-10, newX+10, newY+19,fill="red")
    for group in manager.groups:
        for idVal in hitbox:
            objectType=manager.getObject(group,idVal)
            #print(objectType) 
            if objectType==6 or objectType==8 or objectType==9 or objectType==10 or objectType==11:
                pass
            elif objectType!=0 and objectType is not None and objectType!=4 and objectType!=5:#None is if the id does not exsist in this group
                #Can't be sand, None, or a chest.
                return True
            
    return False#No collision

def onChest(x,y):
    '''
    Checks if the player is on an unopened chest
    '''
    global manager
    hitbox=screen.find_overlapping(x-15, y-15, x+15, y+15)
    
    for group in manager.groups:
        for idVal in hitbox:
            objectType=manager.getObject(group,idVal)
            # print(objectType) 
            if objectType==4:
                return (True,idVal)#On chest
    return (False,None)#Not on chest


def createTextBox(desc,upgrade,price):
    '''
    This function creates a text box for an upgrade
    '''
    upgradeBox=screen.create_rectangle(150,400,350,500,fill="#8c662d")
    upgradeTitle=screen.create_text(250,420,text="Buy "+upgrade+" (enter)",font=("arial",12,"bold"))
    upgradeDesc=screen.create_text(250,450,text=desc,font=("arial",14))
    upgradePrice=screen.create_text(250,470,text="Price: "+str(price),font=("arial",15))
    return (upgradeBox,upgradeTitle,upgradeDesc,upgradePrice)

def checkOnUpgrade(x,y):
    '''
    Checks if you're on top of an upgrade, and removes/creates a text box accordingly. 
    '''
    global manager,grid,upgradeBox,upgradeTitle,upgradeDesc,upgradePrice,upgradeVisible
    global potionPrice,knockbackPrice,swingSpeedPrice,raPrice#Prices
    global currentUpgrade
    
    hitbox=screen.find_overlapping(x-15,y-15,x+15,y+15)
    
    if grid.potion in hitbox:
        if not upgradeVisible:
            upgradeBox,upgradeTitle,upgradeDesc,upgradePrice=createTextBox("Restores 50 health","Health Potion",potionPrice)
            upgradeVisible=True
            currentUpgrade="Potion"

    elif grid.knockbackUpgrade in hitbox:
        if not upgradeVisible:
            upgradeBox,upgradeTitle,upgradeDesc,upgradePrice=createTextBox("Increases knockback","Knockback",knockbackPrice)
            upgradeVisible=True
            currentUpgrade="Knockback"

    elif grid.swingSpeedUpgrade in hitbox:
        if not upgradeVisible:
            upgradeBox,upgradeTitle,upgradeDesc,upgradePrice=createTextBox("Increases sword speed","Sword Speed",swingSpeedPrice)
            upgradeVisible=True
            currentUpgrade="Speed"

    elif grid.ra in hitbox:
        if not upgradeVisible:
            upgradeBox,upgradeTitle,upgradeDesc,upgradePrice=createTextBox("A mysterious artifact","Eye of Ra",raPrice)
            upgradeVisible=True
            currentUpgrade="Ra"
    else:
        if upgradeVisible:
            screen.delete(upgradeBox,upgradeTitle,upgradeDesc,upgradePrice)
            upgradeVisible=False
        currentUpgrade=None

def buyUpgrade(event):
    '''
    What purchases the upgrade and updates the various variables
    Also changes the price and redraws the text boxes
    '''
    global gold,health,startHealth,knockback,swingSpeed,currentUpgrade,hasRa
    global potionPrice,knockbackPrice,swingSpeedPrice,raPrice
    global upgradeBox,upgradeTitle,upgradeDesc,upgradePrice
    if currentUpgrade is None:
        return#Not on an upgrade square

    if currentUpgrade=="Potion":
        if gold>=potionPrice:
            gold-=potionPrice
            health=min(startHealth,health+50)
        
            
    elif currentUpgrade=="Knockback":
        if gold>=knockbackPrice:
            gold-=knockbackPrice
            knockback+=1
            knockbackPrice=round(knockbackPrice*1.5)

            #Need to redraw with new price
            screen.delete(upgradeBox,upgradeTitle,upgradeDesc,upgradePrice)
            upgradeBox,upgradeTitle,upgradeDesc,upgradePrice=createTextBox("Increases knockback","Knockback",knockbackPrice)

    elif currentUpgrade=="Speed":
        if gold>=swingSpeedPrice:
            gold-=swingSpeedPrice
            swingSpeed+=2#Subject to change
            swingSpeedPrice=round(swingSpeedPrice*1.5)
            screen.delete(upgradeBox,upgradeTitle,upgradeDesc,upgradePrice)
            upgradeBox,upgradeTitle,upgradeDesc,upgradePrice=createTextBox("Increases sword speed","Sword Speed",swingSpeedPrice)


    elif currentUpgrade=="Ra" and not hasRa:
        if gold>=raPrice:
            gold-=raPrice
            hasRa=True

    


def calculateAngle():
    '''
    Finds angle from player and mouse
    '''
    global playerSpriteLocation,mouseX,mouseY
    dx=mouseX-playerSpriteLocation[0]
    dy=mouseY-playerSpriteLocation[1]
    angle=degrees(atan2(dy,dx))#atan2 handles direction without if statements
    return angle
        
        
def drawSwordArc(startAngle,endAngle,length=50,arcWidth=10,segments=10):
    global playerSpriteLocation
    '''
    Draw the sword
    From startAngle to endAngle, use lots of small lines to find good points.
    '''
    points=[] 

    #Generate points along the arc
    for i in range(segments+1):#1 to include the endpoint
        angle=radians(startAngle + i*(endAngle-startAngle)/segments)
        x=playerSpriteLocation[0]+cos(angle)*length
        y=playerSpriteLocation[1]+sin(angle)*length
        points.extend([x, y])

    #Draw smaller arc at bottom
    for i in range(segments,-1,-1):
        angle=radians(startAngle + i*(endAngle-startAngle)/segments)
        x=playerSpriteLocation[0]+cos(angle)*(length-arcWidth)
        y=playerSpriteLocation[1]+sin(angle)*(length-arcWidth)
        points.extend([x, y])


    arcId=screen.create_polygon(points,fill="silver",outline="")
    return arcId

def loadArrow():
    '''
    Loads the arrow image so it doesn't get delted
    '''
    global arrowImage
    arrowImage=Image.open("arrow.png").resize((50,50))


def updateArrow():
    '''
    Updates the arrow, redraws with proper angle pointing in right direction
    '''
    global hasRa,playerSpriteLocation,playerPos,grid,arrowId,arrowImage,rotatedArrow

    if not hasRa:
        if arrowId is not None:
            screen.delete(arrowId)
            arrowId=None
        return
    
    bossRow,bossCol=grid.bossCoords    
    playerRow,playerCol=playerPos

    dRow=bossRow-playerRow
    dCol=bossCol-playerCol

    # Calculate angle in degrees
    angle=degrees(atan2(dRow,dCol))

    # Rotate the arrow image
    rotatedArrow=arrowImage.rotate(-angle)  # Negative angle because PIL rotates clockwise
    
    rotatedArrow=ImageTk.PhotoImage(rotatedArrow)
    
    arrowOffset=200 #Distance from the player to display the arrow
    playerX,playerY=playerSpriteLocation

    arrowX=playerX+cos(radians(angle))*arrowOffset

    arrowY=playerY+sin(radians(angle))*arrowOffset

    #Update or create the arrow
    if arrowId==None:
        arrowId=screen.create_image(arrowX, arrowY, image=rotatedArrow, anchor="center")
    else:
        screen.coords(arrowId, arrowX, arrowY)
        screen.itemconfig(arrowId, image=rotatedArrow)

    screen.tag_raise(arrowId)


def animateSword(angle,length=50,arcWidth=10):
    global isSwordSwing,curSwordId,enemyManager,swingSpeed
    '''
    Animate the sword
    '''

    startAngle=angle-60#Start the swing from -60 degrees
    endAngle=angle+60#End the swing at +60 degrees
    #Update swing in steps
    #Use recurisve-esque function for animation because tkinter is stupid, and it won't work otherwise
    def swingStep(curStart):
        nonlocal startAngle,endAngle#These are just defineed outside the function, not global
        global isSwordSwing,curSwordId
       
        isSwordSwing=True
        #Erase the previous arc and draw the new one
        arcId=drawSwordArc(curStart,curStart+30,length,arcWidth)
        curSwordId=arcId
        root.after(50, lambda: screen.delete(arcId))#Delete the arc after a delay


        #Increase angle for the next step
        curStart+=swingSpeed
        if curStart<=endAngle:#Continue until the swing is complete
            root.after(50,lambda: swingStep(curStart))
        if curStart>endAngle:

            isSwordSwing=False

    swingStep(startAngle)
    




def swingSword(event):
    '''
    When you swing your sword, calcultes the angle and animates it
    '''
    global playerSpriteLocation,isSwordSwing,gameStart
    if gameStart:#So you don't swing in intro screen
        #Calculate the angle between player and mouse
        angle=calculateAngle()

        #Animate the sword swing
        if not isSwordSwing:#To prevent more than 1 swing
            animateSword(angle)



def handleKeyPress(event):
    '''
    Handles movement keys
    '''
    global pressedKeys,health
    if event.keysym in ["w","a","s","d"]:
        pressedKeys.add(event.keysym)

        
        
def increaseGold(startX,startY,endX,endY,text):
    '''
    Creates text for the increase in gold
    '''
    dx=(endX-startX)/100
    dy=(endY-startY)/100
    
    curX=startX
    curY=startY
    
    #Recursive-esque function for animation because tkitner is stupid
    def animationStep(curX,curY):
        nonlocal dx,dy,endY
        temp=screen.create_text(curX,curY,text=text,fill="red",font=("arial",12,"bold"))
        
        root.after(1, lambda:screen.delete(temp))
        
        curX+=dx
        curY+=dy
        if curY>endY:
            root.after(1, lambda: animationStep(curX,curY))
    animationStep(curX,curY)

  
        
    
def openChest(event):
    '''
    Opens the chest the player is at
    Updates the 2d array in Grid object and 
    updates objectManager accordinly
    '''
    global manager,gold,playerSpriteLocation,playerPos,viewingLocation,health,edgeLocation,grid
    chestCheck=onChest(playerSpriteLocation[0],playerSpriteLocation[1])
        
    if chestCheck[0]:
        idVal=chestCheck[1]
        x,y=screen.coords(idVal)#Gets coordinate of the chest
        #Update 2d level array
  
        relativePlayerPos=playerPos[:]#To check if the chest is in another square. Need this to update 2d array properly
        
        if viewingLocation[0]<0:
            relativePlayerPos[1]=playerPos[1]-1
            
        elif viewingLocation[0]>500:
            relativePlayerPos[1]=playerPos[1]+1
        
        if viewingLocation[1]<0:
            relativePlayerPos[0]=playerPos[0]-1
        elif viewingLocation[1]>500:
            relativePlayerPos[0]=playerPos[0]+1
        

        curLevel=grid.grid[tuple(relativePlayerPos)]


        #Can't recreate the issue right now
        #Figure out later, works like 99% of the time
        # if idVal not in grid.chestLocations[tuple(relativePlayerPos)]:
        #     print("huh")
        #     print(grid.chestLocations[tuple(relativePlayerPos)])
        #     for row in curLevel:
        #         print(" ".join(map(str,row)))
        #     row,col=0,0
        # else:

        col,row=grid.chestLocations[tuple(relativePlayerPos)][idVal]
        
        curLevel[row][col]=5

        grid.grid[tuple(relativePlayerPos)]=curLevel

        screen.delete(idVal)
        
        
        openChest=grid.resizeImage("openedChest.png",50,50)
        openChestId=screen.create_image(x,y,image=openChest,anchor="nw")
        
        goldGot=randint(3,12)
               

        #groupName,objectId,newObjectId,newObjectType
        manager.editObject(tuple(relativePlayerPos),idVal,openChestId,5)

        gold+=goldGot
        # print("Chest opened")
        
        
        
        
def moveMouse(event):
    '''
    Just updates the mouse x and y
    '''
    global mouseX,mouseY
    mouseX,mouseY=event.x,event.y
    

def handleKeyRelease(event):
    '''
    If you release a key, remove it from the set
    '''
    global pressedKeys
    if event.keysym in ["w","a","s","d"]:
        pressedKeys.discard(event.keysym)
        
def moveScreen(dx, dy):
    '''
    Move the background based on dx and dy
    Also checks if you're on the edge, and whether you should be able to move player sprite or not.
    If you can move the player sprite, don't move the background
    '''
    global viewingLocation, playerPos, playerSpriteLocation, grid,edgeLocation,resetEdgeLocation,playerMovement

    #Check if player is on edge of grid,
    onLeftEdge=(playerPos[1]==0)
    onRightEdge=(playerPos[1]==grid.n-1)
    onTopEdge=(playerPos[0]==0)
    onBottomEdge=(playerPos[0]==grid.n-1)

    #Background movement flags
    moveBackgroundHorizontally=True
    moveBackgroundVertically=True

    #Calculate new player positions
    newX=playerSpriteLocation[0]-dx
    newY=playerSpriteLocation[1]-dy

    # Horizontal background scrolling
    if onLeftEdge:#Moving right on the left edge
        if newX<=250:
            if viewingLocation[0]<=250:#This is to fix the issue when you're on the edge, you move to the right and then the left, but then it doesn't scroll
                moveBackgroundHorizontally=False
                if playerSpriteLocation[0]<=250 and newX>=0:
                    playerSpriteLocation[0]=newX
            
    elif onRightEdge:#Moving left on the right edge
        if newX>=250:
            if viewingLocation[0]>=250:
                moveBackgroundHorizontally=False
                if playerSpriteLocation[0]>=250 and newX<=500:
                    playerSpriteLocation[0]=newX
            

    # Vertical background scrolling
    if onTopEdge:#Moving down on the top edge
        if newY<=250:
            if viewingLocation[1]<=250:
                moveBackgroundVertically=False
                if playerSpriteLocation[1]<=250 and newY>=0:
                    playerSpriteLocation[1]=newY
                

    elif onBottomEdge:#Moving up on the bottom edge
        if newY>=250:
            if viewingLocation[1]>=250:
                moveBackgroundVertically=False
                if playerSpriteLocation[1]>=250 and newY<=500:
                    playerSpriteLocation[1]=newY
            

    #Move the background horizontally if allowed

    
    if moveBackgroundHorizontally:
        viewingLocation[0]-=dx
        playerMovement[0]+=dx#Add because we inversed it when we passed it here.
        for group in manager.groups:
            manager.moveGroup(group,dx,0)
    
    #Move the background vertically if allowed
    if moveBackgroundVertically:
        viewingLocation[1]-=dy
        playerMovement[1]+=dy#Add because we inversed it when we passed it here.
        for group in manager.groups:
            manager.moveGroup(group,0,dy)


def updatePlayerPosition():
    '''
    This function is what actually moves the player. 
    First makes sure there is no diagonal movments.
    Then updates if you're on an upgrade location
    Then checks for any collisions, and moves screen, and dynamically loads anything it if needs to.
    Inverses dx and dy since backgruond moves in opposite direction

    Schedules next update as well, since we need to be constantly running this
    '''
    global playerSpriteLocation,playerMovement,updatePlayerId


    dx,dy=0,0

    #Prevent diagonal movement
    if "a" in pressedKeys and "d" not in pressedKeys:
        dx=-10
    elif "d" in pressedKeys and "a" not in pressedKeys:
        dx=10
    elif "w" in pressedKeys and "s" not in pressedKeys:
        dy=-10
    elif "s" in pressedKeys and "w" not in pressedKeys:
        dy=10

    #Check for collisions and move the player
    newX,newY=playerSpriteLocation[0]+dx,playerSpriteLocation[1]+dy
    checkOnUpgrade(newX,newY)

    
    if not checkCollision(newX, newY):
        moveScreen(-dx,-dy)#Inverse directions because screen moves in opposite direction
        dynamicLoad()#Loads again dynamically
        # sleep(1)

    #Schedule the next update
    updatePlayerId=root.after(50,updatePlayerPosition)



def updateEnemy():
    '''
    Updates the enemy data
    Moves the enemies towards the player and updates enemy
    Also updates gold and health accordingly

    Schedules updates, since this also needs to run constatnyl
    '''
    global curSwordId,gold,knockback,playerId,health,enemySpeed,updateEnemyId
    # print(curSwordId)

    
    enemyManager.moveEnemys(playerPos[0],playerPos[1],playerSpriteLocation,enemySpeed)
    checkUpdate=enemyManager.updateEnemy(playerPos[0],playerPos[1],curSwordId,playerId,knockback,isSwordSwing)
    
    
    if checkUpdate is not None:
        gold+=checkUpdate[0]
        health-=checkUpdate[1]
    updateEnemyId=root.after(50,updateEnemy)





def dynamicLoad():
    '''
    This is one of the most important functiosn of the game. Spent a ton of time here
    
    What this does, is that it first checks if you've moved in a new location
    If you have, it will then unload all enemies that were chasing you.

    It will then calculate what squares you should load, and their relative offset
    I say relative offset, since it assumes that you as a player has not moved. This will be adressed later.

    Use the playerMovement variable, I account for any player movment and load the proper squares accounting for player movment
    I then say that I want to unload the square that was in the inverse direction, as this will not be in direct access.
    I then unload those squares specifically

    Finally, I reset viewingLocation so it fits in a proper range. I also reset playerMovement.

    '''
    global viewingLocation,manager,grid,playerPos,edgeLocation,playerSpriteLocation,playerMovement
    global enemyManager


    rowChange=floor((viewingLocation[1]-250)/(grid.n*50))
    colChange=floor((viewingLocation[0]-250)/(grid.n*50))


    if viewingLocation[1]<250:#To adjust when we are moving left and up. Since viewingLocation will be decreasing, can't do the same check.
        # rowChange=-1*int((viewingLocation[1]*-1+500) // (grid.n * 75)) 
        rowChange=-1*floor((viewingLocation[1]*-1+500)/(grid.n*75))
    if viewingLocation[0]<250:
        # colChange=-1*int((viewingLocation[0]*-1+500) // (grid.n * 75))
        colChange=-1*floor((viewingLocation[0]*-1+500)/(grid.n*75))

    # if (rowChange,colChange)!=(0,0):
    #     print((rowChange,colChange))

    currentRow=rowChange+playerPos[0]
    currentCol=colChange+playerPos[1]

    # print(f"[DEBUG] Current row/col: {currentRow}, {currentCol}")
    # print(f"[DEBUG] Loaded grid keys: {list(grid.grid.keys())}")
    # print(f"[DEBUG] Loaded manager groups: {list(manager.groups.keys())}")

    #CurrentRow,currentCol will always exsist
    if [currentRow,currentCol]!=playerPos and 0<=currentRow<grid.n and 0<=currentCol<grid.n:
        
        
        oldRow,oldCol=playerPos[0],playerPos[1]
        enemyManager.unloadEnemies(oldRow,oldCol)#Unload the enmies from the previous one


        # print((rowChange,colChange))

        if (rowChange,colChange)==(0,-1):#These are the locations where we have to load the values
            #Left
            load=[(1,-1), (0,-1), (-1,-1)]
            offset=[(-500,500),(-500,0),(-500,-500)]
            
        elif (rowChange,colChange)==(0,1):
            #Right
            load=[(-1,1),(0,1),(1,1)]
            offset=[(500,-500),(500,0),(500,500)]

        elif (rowChange,colChange)==(-1,0):
            #Up
            load=[(-1,0),(-1,1),(-1,-1)]
            offset=[(0,-500),(500,-500),(-500,-500)]
            
            
        elif (rowChange,colChange)==(1,0):
            #Down
            load=[(1,0),(1,-1),(1,1)]
            offset=[(0,500),(-500,500),(500,500)]
            
            
            

        unload=[]
        for i in range(len(load)):
            rowOffset,colOffset=load[i]
            loadRow,loadCol=currentRow+rowOffset, currentCol+colOffset
            #Need to load this location
            # print((loadRow,loadCol))

            # if (loadRow,loadCol) in manager.groups:
            #     print(f"[DEBUG] Already loaded: {loadRow}, {loadCol}")

            if 0<=loadRow<grid.n and 0<=loadCol<grid.n and (loadRow,loadCol) not in manager.groups:#Ensure in bounds 
                #Figure out offsets and I should be good
                # print((loadRow,loadCol))

                if (loadRow,loadCol) not in grid.grid:
                    grid.generateLevel(loadRow,loadCol)
                    
                
                    
                #playerMovment[0] is x movment, playerMovement[1] is y movement
                xOffset=offset[i][0]
                yOffset=offset[i][1]

                if playerMovement[0]<0:
                    xOffset-=abs(playerMovement[0])%500
                else:
                    xOffset+=playerMovement[0]%500
                
                if playerMovement[1]<0:
                    yOffset-=abs(playerMovement[1])%500
                else:
                    yOffset+=playerMovement[1]%500


                grid.drawLevel(loadRow, loadCol, enemyManager,manager,xOffset,yOffset)
                
                # print(f"[DEBUG] Loading level: {loadRow}, {loadCol}")
                # print(f"[DEBUG] Offset: {xOffset}, {yOffset}")

                
                
                unload.append((rowOffset*-1,colOffset*-1))
            
            else:
                pass
                #Out of range, so remove from unload, want to keep them loaded
                # print(f"[DEBUG] Not loading: {loadRow}, {loadCol}")
                

        for rowOffset, colOffset in unload:
            unloadRow,unloadCol=oldRow+rowOffset,oldCol+colOffset
            if (unloadRow,unloadCol) in grid.grid and (unloadRow,unloadCol) in manager.groups and (unloadRow,unloadCol)!=(currentRow,currentCol) :
                manager.deleteGroup((unloadRow,unloadCol))
                
                # print(f"[DEBUG] Unloading level: {unloadRow}, {unloadCol}")
                # print((unloadRow,unloadCol))


        #Okay, for loading it is the inverse of the offset. Multiply everything in offset by -1
        # print("LOADING:")
        # print(f"Going to: {(currentRow,currentCol)}")

        # print()
        playerPos=[currentRow,currentCol]
        
        enemyManager.loadEnemies(playerPos[0],playerPos[1])
        if viewingLocation[0]==-250 or viewingLocation[0]==750:
            viewingLocation[0]=250
            playerMovement[0]=0#Resets it
        if viewingLocation[1]==-250 or viewingLocation[1]==750:
            viewingLocation[1]=250
            playerMovement[1]=0#Resets it
 


def winAnimation():
    '''
    This runs the animation when you win the game. Lots of functions within functions here, since it is a 2-step animation

    This also creates the replay screen when you win
    '''
    global sandImage,playerImage#So it doesn't get deleted

    screen.create_oval(50,50,100,100,fill="red")

    sandImage=Image.open("sand.png").resize((50,50))
    sandImage=ImageTk.PhotoImage(sandImage)

    playerImage=Image.open("player.png").resize((40,40))
    playerImage=ImageTk.PhotoImage(playerImage)
    
    eyeOfRa=Image.open("justRa.png").resize((102,82))
    eyeOfRa=ImageTk.PhotoImage(eyeOfRa)


    for i in range(10):#Draws sand background
        for j in range(10):
            screen.create_image(j*50,i*50,image=sandImage,anchor="nw")
    playerX,playerY=250,500

    
    def movePlayerUp(playerY):#Animation to move the player up towards the center
        nonlocal playerX
        temp=screen.create_image(playerX,playerY,image=playerImage)

        root.after(10,lambda:screen.delete(temp))

        playerY-=1

        if playerY>250:
            root.after(10,lambda:movePlayerUp(playerY))
        else:
            screen.create_image(playerX,200,image=eyeOfRa)
            screen.create_image(playerX,playerY,image=playerImage)
            root.after(2000,lambda:raAura(0))#After 2 seconds run the next animation

    def raAura(size):#Increase yellow circle around eye of Ra
        nonlocal playerX
        temp=screen.create_oval(playerX-size,200-size,playerX+size,200+size,fill="yellow")
        root.after(10,lambda:screen.delete(temp))

        size+=5
        if size<500:
            root.after(10,lambda:raAura(size))
        else:
            screen.create_oval(playerX-size,200-size,playerX+size,200+size,fill="yellow",outline="")
            #Play again:
            screen.create_text(250,250,text="You Won!",font=("arial",36,"bold"),fill="green")
            screen.create_text(250,300,text="Congratulations!",font=("arial", 16),fill="black")

            playAgainButton=Button(root,text="Play Again",font=("arial", 14),command=lambda: introScreen())
            screen.create_window(250,350,window=playAgainButton)

    movePlayerUp(playerY)#Start the animation
    



def introScreen():
    '''
    Display intro and difficulty selection screen
    Initalize values here, since otherwise, if you try to input things it errors.
    '''
    global introImage#So the image isn't deleted
    initalizeValues()#Should reset everything

    screen.delete("all")


    introImage=Image.open("startGame.png").resize((500,500))
    introImage=ImageTk.PhotoImage(introImage)
    screen.create_image(0,0,image=introImage,anchor="nw")
   
    # spacing = 50

    # for x in range(50, 1000, spacing): 
    #     screen.create_line(x, 25, x, 1000, fill="blue")
    #     screen.create_text(x, 5, text=str(x), font="Times 10", anchor = N, fill="black")
    
    # for y in range(50, 1000, spacing):
    #     screen.create_line(25, y, 1000, y, fill="blue")
    #     screen.create_text(5, y, text=str(y), font="Times 10", anchor = W, fill="black")

    easyButton=Button(root,text="Easy",font=("Arial", 14),command=lambda:startGame("easy"))
    mediumButton=Button(root,text="Medium",font=("Arial", 14),command=lambda:startGame("medium"))
    hardButton=Button(root,text="Hard",font=("Arial", 14),command=lambda:startGame("hard"))

    # Place buttons on the canvas
    screen.create_window(400,350,window=easyButton)
    screen.create_window(400,400,window=mediumButton)
    screen.create_window(400,450,window=hardButton)


def startGame(difficulty):
    '''
    This fucntion updates the values based on difficulty. The harder it gets, the less health you gett and the faster the enemies get
    '''
    global health,enemySpeed,startHealth


 
    if difficulty=="easy":
        enemySpeed=3
        health=150
        startHealth=health

    elif difficulty=="medium":
        enemySpeed=4
        health=100
        startHealth=health

    elif difficulty=="hard":
        enemySpeed=4
        health=75
        startHealth=health

    screen.delete("all")
    runGame()


def runGame():
    '''
    Of course this is the function that runs the game itself
    '''

    global playerId,gameStart#Because we modify them here

    
    gameStart=True#Just to make sure that you can't swing on intro screen
    
    # print(grid.blackMarketCoords)
    # print(grid.bossCoords)
    # sleep(4)
    grid.generateLevel(4,4)#Spawning location
    grid.drawLevel(4,4,enemyManager,manager)#Draw level
    grid.drawSurrounding(4,4,enemyManager,manager)#Draw surrounding


    # print(manager.groups)


    playerImage=Image.open("player.png").resize((40,40))
    playerImage=ImageTk.PhotoImage(playerImage)
    
    diamondImage=Image.open("diamond.png").resize((50,50))
    diamondImage=ImageTk.PhotoImage(diamondImage)
    
    heartImage=Image.open("heart.png").resize((75,75))
    heartImage=ImageTk.PhotoImage(heartImage)

    
    
    cur=gold
    updatePlayerPosition()
    updateEnemy()
    loadArrow()
    
    startHealth=health
    while health>0:
        if hasRa:
            updateArrow()
            #Has eye of ra, so update the arrow position




        if tuple(playerPos)==grid.bossCoords and hasRa:
            #You're at the win location
            break


        if gold!=cur:#Updates gold text 
            goldGot=gold-cur
            x,y=playerSpriteLocation
            x+=randint(-10,10)
            if goldGot<0:
                increaseGold(x,y-20,x,y-40,"- "+str(abs(goldGot)))
            else:
                increaseGold(x,y-20,x,y-40,"+ "+str(goldGot)) 
            cur=gold

        
        player=screen.create_image(playerSpriteLocation[0],playerSpriteLocation[1],image=playerImage)
        playerId=player#Updates playerid, when we redraw it
        
        diamond=screen.create_image(40,75,image=diamondImage)
        
        diamondText=screen.create_text(100,75,text=gold,font=("Courier New",24))
       
        healthBar=screen.create_rectangle(65,15,65+(startHealth*2),35,fill="gray",outline="")

        healthDisplay=screen.create_rectangle(65,15,max(65,65+health*2),35,fill="green",outline="")

        heart=screen.create_image(35,25,image=heartImage)
        
        location=screen.create_text(65,100,text="ROW: "+str(playerPos[0])+" COL: "+ str(playerPos[1]),fill="white",font=("arial",12,"bold"))
        # debugDisplay=screen.create_text(50,120,text=str(viewingLocation),fill="white")

        screen.update()
        screen.delete(player,diamond,diamondText,heart,healthDisplay,healthBar,location)

    if health<=0:
        #You lost the game
        #Need to reset everything
        screen.delete("all")

        grid.reset()
        enemyManager.reset()
        root.after_cancel(updateEnemyId)#Stop the continous update checks. What broke the speed before
        root.after_cancel(updatePlayerId)

        screen.create_text(250,250,text="Game Over!",font=("arial",36,"bold"),fill="red")
        screen.create_text(250,300,text="You lost the game. Better luck next time!",font=("arial", 16),fill="white")

        playAgainButton=Button(root,text="Play Again",font=("arial", 14),command=lambda: introScreen())
        screen.create_window(250,350,window=playAgainButton)

    else:
        #You won!
        #Create win animation
        screen.delete("all")

        grid.reset()
        enemyManager.reset()
        root.after_cancel(updateEnemyId)#Stop the continous update checks. What broke the speed before
        root.after_cancel(updatePlayerId)

        winAnimation()


root.after(500,introScreen)
screen.pack() 


screen.bind("<KeyPress>",handleKeyPress)
screen.bind("<KeyRelease>",handleKeyRelease)
screen.bind("<Motion>",moveMouse)
screen.bind("<space>",swingSword)
screen.bind("<e>",openChest)
screen.bind("<Return>",buyUpgrade)

screen.focus_set() #makes Python pay attention to mouse clicks and button pushes
screen.mainloop()