from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from analyze_exercise import analyze_pushup, score_pushup, detect_pushup_reps
import requests
import json

TOKEN = "7802077777:AAEJQSKHimGgnjrKT6ImjgB1dsus6JX618g"

leaderboard = {}

async def start(update: Update, context):
    await update.message.reply_text("Welcome to the AI Fitness Challenge!")

async def handle_message(update: Update, context):
    await update.message.reply_text("I received your message!")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


llm_api_key = "AIzaSyBA-229EC9mTgBDb_bqhFY3Hqk6OU29Ygk"
def generate_pushup_feedback(score):


    response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={llm_api_key}",
        json={
            "contents": [{
                "parts": [{"text": f"My pushup score is {score}/100. Give me 3 improvement tips not exceeding 10 words each."}]
            }]
        }
    )

    # response = openai.ChatCompletion.create(
    #     model="gpt-4-vision-preview",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    return json.loads(response.text)["candidates"][0]["content"]["parts"][0]["text"]

    # return response["choices"][0]["message"]["content"]  # Correct indentation

# Example Usage


async def show_leaderboard(update: Update, context):
    """Displays the top users on the leaderboard."""
    if not leaderboard:
        await update.message.reply_text("🏆 No scores yet! Upload a workout video to get started.")
        return

    # Sort leaderboard by score
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1]['score'], reverse=True)

    message = "🏆 *Push-Up Challenge Leaderboard* 🏆\n\n"
    for i, (user_id, data) in enumerate(sorted_leaderboard, 1):
        message += f"{i}. {data['name']} - {data['score']} points ({data['videos']} videos)\n"

    await update.message.reply_text(message)


async def handle_video(update: Update, context: CallbackContext):

    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    video_file = update.message.video.file_id
    video = await context.bot.get_file(video_file)
    await video.download_to_drive("workout.mp4")

    # Analyze push-up form
    angles_list = analyze_pushup("workout.mp4")
    reps_wise_angles = detect_pushup_reps(angles_list)
    score = score_pushup(reps_wise_angles)

    if user_id not in leaderboard:
        leaderboard[user_id] = {
            "name": user_name,
            "score": score
        }
    else:
        leaderboard[user_id]["score"] = score

    if score < 75:
        await update.message.reply_text(f"Your push-up form score: {score:.2f}/100 💪. Curating improvement tips...")
        feedback = generate_pushup_feedback(score)
        await update.message.reply_text(f"Here is how you can improve your pushups::: {feedback}")
    else:
        await update.message.reply_text(f"Your push-up form score: {score:.2f}/100 💪. You are doing great! Keep it up!")

app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(CommandHandler("leaderboard", show_leaderboard))

print("Bot is running...")
app.run_polling()
