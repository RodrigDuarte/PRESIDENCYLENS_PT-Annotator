# Annotator Rules

The goal of this annotation task is to determine whether an image is relevant(1) or irrelevant(0) to a given query. Relevance is defines by the relationship between the query, the image, and the context provided by the article title.

## Guidelines

1. **Understanding the query**: Read the query carefully. Identify the key terms and concepts. Consider the intent behind the query. What information is the user seeking?
1. **Evaluating the image**: Assess the content of the image. Does it depict something that is related to the query? Look for visual elements (People, objects, actions, places...) that can be linked to the query.
1. **Context from the article title**: Read the article title provided since it may help clarify the context of the image. It helps in situations where the query might depict a specific event, person or object that is mentioned in the title.
1. **Labeling the image**: Based on your assessment, label the image as relevant (1) or irrelevant (0). Use the following criteria to guide your decision:
    - **Relevant (1)** - The image directly supports, illustrates or is related to the query. It should provide meaningful context or information that aligns with the query's intent.
    - **Irrelevant (0)** - The image does not support or relate to the query in a meaningful way. It may be unrelated, misleading, or provide no additional context to the query.
1. **Common scenarios**:
    - **Direct match**: if the image clearly depicts the subject, place, action or object mentioned in the query, it is relevant.
    - **Indirect match**: if the image depicts something that could be related to the query but not in an obvious way, consider the context provided by the article title. If the image is related to the article title and could be relevant to the query, it is relevant.
    - **Unrelated content**: If the image shows something completely different from the query and does not provide any context or information related to the query, it is irrelevant.
    - **Ambiguous cases**: If in doubt even after using the article title as context, choose the image as irrelevant. The subject of the image should be clearly shown in the image, for instance, if the image is blurry or too small to identify the subject, it is irrelevant. For people, the face should be clearly visible and identifiable, when the subject is to the side or not clearly visible, it is irrelevant.
1. **Avoiding biases**: Try to be objective and avoid personal biases. Focus on the content of the image and its relationship to the query. Do not let personal opinions or feelings about the subject matter influence your decision.
1. **Unknown terminology**: If you encounter a term or concept in the query or article title that you do not know, you can search for it online to understand its meaning. This can help you better assess the relevance of the image.

## How does the annotation process work?

1. In the interface, you will see a query, the article title for the image, and the image itself.
2. Read the query and the article title carefully.
3. Evaluate the image based on the guidelines provided above.
4. Select the appropriate label (1 for relevant, 0 for irrelevant) based on your assessment. You can use the buttons on the interface or the keys on your keyboard "R" for relevant and "I" for irrelevant.
5. After selecting the label, the next image will show up automatically. (Keep in mind that the query and article title can change, so be sure to read them carefully each time.)

>Note: If you made a mistake you can undo by clicking the "Undo" button or using the keyboard shortcut "Z". The progress is saved automatically and you can leave at any time. There is also a progress bar to track how many images you have annotated for the current query.
