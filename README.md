скачать ollama локально (Linux)

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

спулить модель 

```bash
ollama pull llama3:8b-instruct-q3_K_M 
```

проверить что модель дейтствительно существует

```bash
ollama list 
```

будет вот такой вывод

```
NAME                         ID              SIZE      MODIFIED       
llama3:8b-instruct-q3_K_M    726a1960bfed    4.0 GB    52 minutes ago 
```

запусть локальный сервер с ollama на порту 11434

```bash
ollama serve
```

можно проверить работу через запрос

```
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "llama3:8b-instruct-q3_K_m",
  "prompt": "Why is the sky blue?"
}'
```

Тестовые вопросы:

- Насколько выше доход у фрилансеров, принимающих оплату в криптовалюте, по сравнению с другими способами оплаты?
- Как распределяется доход фрилансеров в зависимости от региона проживания?
- Какой процент фрилансеров, считающих себя экспертами, выполнил менее 100 проектов?


Категориальные:
Job_Category - Web Development, App Development, Data Entry, Digital Marketing, Customer, Support, Content Writing, Graphic Design, SEO
Platform - Fiverr, PeoplePerHour, Upwork, Toptal, Freelancer
Experience_Level - Beginner, Intermediate, Expert
Client_Region - Asia, Australia, UK, Europe, USA, Middle East, Canada
Payment_Method - Mobile Banking, Crypto, Bank Transfer, PayPal
Project_Type - Fixed, Hourly

Остальные:
Freelancer_ID, Job_Completed,Earnings_USD,Hourly_Rate,Job_Success_Rate,Client_Rating,Job_Duration_Days,Rehire_Rate,Marketing_Spend
