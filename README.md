🧠 Subjective Answer Evaluation System (SAE)

A Django-based web application designed to evaluate subjective answers automatically using NLP techniques. The system helps educational institutions streamline the grading process, improve consistency, and reduce manual efforts.

🚀 Features

- Student registration and login
- Instructor/admin panel
- NLP-based answer evaluation
- Grading based on similarity with ideal answers
- SQLite database support
- Ready for deployment (Heroku supported)


🛠️ Tech Stack

- **Backend:** Django (Python)
- **Frontend:** HTML/CSS, Django Templates
- **Database:** SQLite
- **Deployment:** Anaconda(VS Code)
- **NLP:** Word2Vec, Cosine Similarity, WMD


📦 Installation & Setup (Using Anaconda)

1. Clone the Repository

```bash
git clone https://github.com/your-username/subjective-answer-evaluation.git
cd subjective-answer-evaluation
```
2. Create a Virtual Environment (Anaconda)

conda create -n sae-env python=3.9
conda activate sae-env

3. Install Dependencies

pip install -r requirements.txt

4. Run Migrations

python manage.py makemigrations
python manage.py migrate

5. Run the Server

python manage.py runserver
Visit: http://127.0.0.1:8000/

🧠 NLP Techniques Used
1.Cosine Similarity
2.Word2Vec Embeddings
3.Word Mover’s Distance (WMD)

- Algorithms are applied to compare student answers with the model answer and assign scores based on semantic similarity.


📸 Screenshots:
![Screenshot (215)](https://github.com/user-attachments/assets/60fbace8-bd26-4747-bb5a-b0ac03648815)
![Screenshot (217)](https://github.com/user-attachments/assets/29875f59-f4ee-4197-9f89-c86cd149ceb7)
![Screenshot (216)](https://github.com/user-attachments/assets/3af0ef4b-db2a-4bd3-b66c-002b01b713c8)
![Screenshot (218)](https://github.com/user-attachments/assets/3549975e-8781-4db9-bff8-90095c6fa8f5)
![Screenshot (225)](https://github.com/user-attachments/assets/b960ee86-0702-49e6-9f87-7574d22cc5e8)
![Screenshot (219)](https://github.com/user-attachments/assets/587a57df-e52e-4e50-ba53-fcec531b6051)
![Screenshot (220)](https://github.com/user-attachments/assets/06169543-9563-4f6c-9861-9c5b8bbbdb3b)
![Screenshot (221)](https://github.com/user-attachments/assets/d5da0f59-9ebe-42b9-88f8-901330a208d0)
![Screenshot (222)](https://github.com/user-attachments/assets/4891fc5c-2996-4dd4-b01f-7fe69c9a010e)




