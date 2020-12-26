from fed_ml.Client import Clients
from fed_ml.Server import Server
from fed_ml.Attacker import Attacker


if __name__ == "__main__":
    """Set hyper-parameters."""
    epoch = 6
    learning_rate = 0.0001
    # The ml_privacy_meter can't handle the scenario with too many participants.
    CLIENT_NUMBER = 5
    # And as federated learning is online,
    # participants are uncertain about their online status in each training epoch.
    CLIENT_RATIO_PER_ROUND = 1.00
    # Some characteristics of the dataset cifar-100.
    input_shape = (32, 32, 3)
    # classes_num = 100   # cifar-100
    classes_num = 10    # cifar-10

    """Build clients, server and attacker."""
    client = Clients(input_shape=input_shape,
                    classes_num=classes_num,
                    learning_rate=learning_rate,
                    clients_num=CLIENT_NUMBER,
                     dataset_path="./datasets/cifar100.txt")
    server = Server()
    attacker = Attacker()

    """Target the attack."""
    target_cid = 1
    target_ep = 2
    attacker.declare_attack("LGAA", target_cid, target_ep)
    attacker.generate_attack_data(client)

    """Specify the local gradient ascent attacker."""
    adversarial_cid = (target_cid + 1) % CLIENT_NUMBER

    """Begin training."""
    for ep in range(epoch):
        server.initialize_local_parameters_sum()
        active_clients = client.choose_clients(CLIENT_RATIO_PER_ROUND)
        for client_id in active_clients:
            client.current_cid = client_id
            print("[fed-epoch {}] cid: {}".format(ep, client_id))
            client.download_global_parameters(server.global_parameters)
            client.train_local_model()
            current_local_parameters = client.upload_local_parameters()
            server.accumulate_local_parameters(current_local_parameters)
            if ep == (target_ep - 1) and client_id == adversarial_cid:
                attacker.generate_target_gradient(client)
                attacker.craft_adversarial_parameters(client)
                print("the adversarial parameters have been crafted.")
            if ep == target_ep and client_id == target_cid:
                print("local gradient ascent attack on cid: {} in fed-epoch: {}".format(client_id, ep))
                attacker.membership_inference_attack(client)
        server.update_global_parameters(len(active_clients))