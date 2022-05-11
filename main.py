import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor, VkKeyboardButton


def main():
    with open("file.txt", 'r') as f:
        vk_session = vk_api.VkApi(token=f.readline())

    vk = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
            print(f'New message from {event.user_id}, text = {event.text}')

            vk.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                keyboard=open("keyboard/default.json", "r").read(),
                message="Привет, " + vk.users.get(user_id=event.user_id)[0]['first_name']
            )


if __name__ == "__main__":
    main()
