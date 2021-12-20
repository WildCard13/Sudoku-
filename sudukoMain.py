print('Setting UP')
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import sudukoSolver
from utlis import *
import streamlit as st
from PIL import Image


def load_image(picture):
    sudoku = Image.open(picture)
    return sudoku


st.set_page_config(layout="wide")
st.title("SUDOKU SOLVER", anchor=None)
image_file = st.file_uploader("Upload The Sudoku Image Here :", type=["jpg", "jpeg"])

if st.button('SOLVE'):
    if image_file is not None:
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        file_details = {"filename": image_file.name,
                        "filetype": image_file.type,
                        "filesize": image_file.size}

        # To View Uploaded Image
        col_org, col_sol = st.columns(2)
        with col_org:
            st.image(load_image(image_file), width=250)
            st.success("Uploaded Image :" + image_file.name)
        ########################################################################
        # pathImage = "Resources/test-4.jpg"
        heightImg = 360
        widthImg = 360
        model = initializePredictionModel()  # LOAD THE CNN MODEL
        ########################################################################
        #  ### 1. PREPARE THE IMAGE

        img = cv2.imdecode(file_bytes, 1)
        img = cv2.resize(img, (widthImg, heightImg))  # RESIZE IMAGE TO MAKE IT A SQUARE IMAGE
        imgBlank = np.zeros((heightImg, widthImg, 3),
                            np.uint8)  # CREATE A BLANK IMAGE FOR TESTING DEBUGGING IF REQUIRED
        imgThreshold = preProcess(img)

        # #### 2. FIND ALL CONTOURS

        imgContours = img.copy()  # COPY IMAGE FOR DISPLAY PURPOSES
        imgBigContour = img.copy()  # COPY IMAGE FOR DISPLAY PURPOSES
        contours, hierarchy = cv2.findContours(imgThreshold, cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)  # FIND ALL CONTOURS
        cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 3)  # DRAW ALL DETECTED CONTOURS

        #  ### 3. FIND THE BIGGEST CONTOUR AND USE IT AS SUDOKU
        biggest, maxArea = biggestContour(contours)  # FIND THE BIGGEST CONTOUR
        print(biggest)
        if biggest.size != 0:
            biggest = reorder(biggest)
            print(biggest)
            cv2.drawContours(imgBigContour, biggest, -1, (0, 0, 255), 25)  # DRAW THE BIGGEST CONTOU
            pts1 = np.float32(biggest)  # PREPARE POINTS FOR WARP
            pts2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])  # PREPARE POINTS FOR WARP
            matrix = cv2.getPerspectiveTransform(pts1, pts2)  # GER
            imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))
            imgDetectedDigits = imgBlank.copy()
            imgWarpColored = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)

            #  ### 4. SPLIT THE IMAGE AND FIND EACH DIGIT AVAILABLE

            imgSolvedDigits = imgBlank.copy()
            boxes = splitBoxes(imgWarpColored)
            print(len(boxes))
            numbers = getPrediction(boxes, model)
            print(numbers)
            imgDetectedDigits = displayNumbers(imgDetectedDigits, numbers, color=(220, 20, 60))
            numbers = np.asarray(numbers)
            posArray = np.where(numbers > 0, 0, 1)
            print(posArray)

            #  ### 5. FIND SOLUTION OF THE BOARD

            board = np.array_split(numbers, 9)
            print(board)
            try:
                sudukoSolver.solve(board)
            finally:
                pass
            print(board)
            flatList = []
            for sublist in board:
                for item in sublist:
                    flatList.append(item)
            solvedNumbers = flatList * posArray
            imgSolvedDigits = displayNumbers(imgSolvedDigits, solvedNumbers)

            #  ### 6. OVERLAY SOLUTION

            pts2 = np.float32(biggest)  # PREPARE POINTS FOR WARP
            pts1 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])  # PREPARE POINTS FOR WARP
            matrix = cv2.getPerspectiveTransform(pts1, pts2)  # GER
            imgInvWarpColored = img.copy()
            imgInvWarpColored = cv2.warpPerspective(imgSolvedDigits, matrix, (widthImg, heightImg))
            inv_perspective = cv2.addWeighted(imgInvWarpColored, 1, img, 0.5, 1)
            imgDetectedDigits = drawGrid(imgDetectedDigits)
            imgSolvedDigits = drawGrid(imgSolvedDigits)

            # imageArray = ([img, inv_perspective])

            imageArray = ([img, imgDetectedDigits, imgSolvedDigits, inv_perspective])
            # [imgDetectedDigits, , imgInvWarpColored, ])

            stackedImage = stackImages(imageArray, 1)
            cv2.imshow('Image Stack', stackedImage)

            with col_sol:
                st.image(inv_perspective, width=250)
                st.success("Solved Image :" + image_file.name)
        else:
            print("No Sudoku Found")

st.button("NEXT")
cv2.destroyAllWindows()
