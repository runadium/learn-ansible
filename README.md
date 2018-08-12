# learn-ansible

## Notre objectif

L'objectif de ce tutorial est d'apprendre à installer une infrastructure complexe grâce à [Ansible](https://docs.ansible.com/ansible/latest/index.html).

## Architecture technique cible

Notre infracstructure sera composé de 5 VMs réparties comme suit:

- **1 x BASTION:** Cette VM va nous servir de point d'accès aux autres machines de l'infra. Ansible sera installé et exécuté sur cette VM.
- **3 x VMs applicatives:** Sur les quelles nous allons installer une application [Spring-Boot](https://spring.io/projects/spring-boot) qui exposera des endpoints REST.
- **1 x VM [HAProxy](http://www.haproxy.org/):** Nous servira de load balancer (Front end) pour les clients.

    Vous pouvez ajuster le nombre de VM si besoin, l'idée reste la même.

![tutorial infra architecture](assets/learn-ansible-infra.png)

## Step 1: Installation de l'environement



### Vagrant

Nous allons utiliser Vagrant pour simuler (par virtualisation) notre infrastructure

#### Installation de Vagrant

#### Plugins à installer

- *vagrant-vbguest* (conseillé) `vagrant plugin install vagrant-vbguest`
- *vagrant-env* (conseillé) `vagrant plugin install vagrant-env`
- *vagrant-timezone* (conseillé) `vagrant plugin install vagrant-timezone`
- *vagrant-proxyconf* (si vous êtes derrière un proxy d'entreprise) `vagrant plugin install vagrant-proxyconf`

#### Démarrer notre infrastructure

```sh
# Dupliquer le fichier .env afin de pouvoir le customiser
cp .env.template .env
# Vérifier les VMs qui vont être crées
vagrant status
# Démarrer les instances
vagrant up

# Se connecter en ssh sur le noeud BASTION
vagrant ssh BASTION-NODE

# Passer en root
sudo su

# Se déplacer dans le répertoire /learn-ansible (qui sera notre répertoire de travail)
mkdir /learn-ansible && cd /learn-ansible
```

Essayez de contacter les noeuds de l'infra (depuis la VM BASTION) pour vérifier le setup

## Step 2: Installer Ansible sur le  BASTION

### Installer le repo epel-release

```sh
yum --enablerepo=extras install -y epel-release
```

### installation de *pip*

```sh
yum -y install -y python-pip git tree java-1.8.0-openjdk-devel
```

### Installation de Ansible

```sh
pip install ansible
```

### Tester l'infrastructure avec Ansible

Nous allons exécuter un `ping` sur tous les noeuds que nous avons dans notre infra.

#### Ping de localhost avec Ansible

```sh
ansible -m ping localhost
```

#### Créer l'inventaire des serveurs dans le fichier /etc/ansible/hosts (fichier inventaire par défaut)

```sh
mkdir /etc/ansible
cat > /etc/ansible/hosts <<EOF

# Default User and password to use
[all:vars]
ansible_user = root
ansible_ssh_pass= vagrant

# Ce group n'est pas obligatoire, il est nécessaire seulement si aucun autre groupe n'est définit
[all]
infra-node-1.infra.local
infra-node-2.infra.local
# Rajoutez autant de serveur que vous en avez

# Permet de cibler uniquement les serveurs du groupe A
[groupA]
infra-node-1.infra.local

# Permet de cibler uniquement les serveurs du groupe B
[groupB]
infra-node-2.infra.local

EOF

cat > ~/.ansible.cfg <<EOF

[defaults]
host_key_checking = False

EOF
```

#### Ping l'ensemble des serveurs avec Ansible

```sh
ansible -m ping  all
```

Le mot de pass root par defaut est `vagrant`. Oui Ansible à besoin des information d'authentification pour pouvoir se connecter en SSH sur les noeuds de notre infrastructure.
Il y'a plusieurs façon de s'authentifier en ssh:

- **user/password**: c'est ma méthode que nous allons utiliser pour faire simple
- **certificats (private/public key)**: Dans la vraie vie vous allez plutôt utiliser des certificats pour vous connecter à vos différents serveurs. Ce n'est pas l'objectif de ce tutorial


Le résultat attendue est le suivant (l'ordre des serveurs n'est pas important):

```sh
[root@bastion ~]# ansible -m ping  all
infra-node-2.infra.local | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
infra-node-1.infra.local | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
[root@bastion ~]#
```

#### Autres exemples de commandes à lancer sur tous nos serveurs

##### Voir la mémoire disponible sur tous les serveurs

```sh
ansible -a "/bin/sh -c 'free -h'"  all
# ou
ansible -m command -a "free -h"  all
# ou pour cibler uniquement un groupe
ansible -m command -a "free -h"  groupA
```

##### Voir l'espace disque disponible sur tous les serveurs

```sh
ansible -a "/bin/sh -c 'df -h'"  all
# ou
ansible -m command -a "df -h"  all
# ou pour cibler uniquement un groupe
ansible -m command -a "df -h"  groupA
```

## Step 3: Préparation de nos différents environnements

Nous allons considérer que nous avons plusieurs environnements cibles (DEV,RECETTE, QUALIF ...), même si dans ce tutorial nous allons traiter que l'environnemment de DEV.

### Création de la structure des environnements

```sh
# Création des dossiers par environnement
mkdir -p environments/dev
mkdir -p environments/qualif
mkdir -p environments/prod

# Création de la structure complète pour l'environnement de dev
mkdir -p environments/dev/group_vars # Ce répertoire contient les variables par groupe
mkdir -p environments/dev/host_vars # Ce répertoire contient les variables par host (machine)

cat > environments/dev/hosts <<EOF

# Default User and password to use
[all:vars]
ansible_user = root
ansible_ssh_pass= vagrant

# Ce group n'est pas obligatoire, il est nécessaire seulement si aucun autre groupe n'est définit
[all]
infra-node-1.infra.local
infra-node-2.infra.local
infra-node-3.infra.local
infra-node-4.infra.local

# Group HaProxy, Pour le tuto l'HAProxy sera installé sur une machine unique comme indiqué dans le schema d'architecture
[ha-proxy]
infra-node-1.infra.local

# Permet de cibler uniquement les serveurs du groupe B
[spring-boot-app]
infra-node-2.infra.local
infra-node-3.infra.local
infra-node-4.infra.local

# Ces notations permettent de définir des groupes à partir de groupes déja existant.
[loadbalancer:children]
ha-proxy

[applis:children]
spring-boot-app

EOF

# Création du répertoire roles qui contiendra les roles (dans notre cas le role ha-proxy que nous allons écrire)
mkdir roles

```

Nous allons travailler essentielement sur l'environnement "dev", pour ça nous allons dire à Ansible d'utiliser ce répertoire comme notre environnement par défaut.

Le fichier **ansible.cfg** permet de configuer le setup ansible. Nous allons créer ce fichier avec le minimum de configuration, nous verrons par la suite à quoi sert chacun de ces paramètres.

```sh
cat > /learn-ansible/ansible.cfg <<EOF

[defaults]
ansible_managed = Please do not modify this file directly as it is managed by Ansible and could be overwritten.
host_key_checking = False

# Inventaire par défaut quand l'environnement n'est pas précisé en ligne de commande.
inventory = ./environments/dev

# Répertoires par défaut qui contiendront nos différents roles.
roles_path = ./galaxy_roles/:./roles/

EOF

```

## Step 4: Installation de l'application Spring boot

### Clone et build du projet

Nous allons utiliser une application spring-boot très basique [simple-springboot-app](https://github.com/runadium/simple-springboot-app) qui expose un endpoint REST.

```sh
# Checkout de l'appli spring boot (pour la builder en local)
git clone https://github.com/runadium/simple-springboot-app.git /simple-springboot-app

cd /simple-springboot-app
# Packager l'application en JAR (service Spring Boot)
./mvnw package
# Vérifier que l'appli a bien été packagé
ls -alrt /simple-springboot-app/target
# On retrouve bien le fichier simple-springboot-app-0.0.1-SNAPSHOT.jar

# Retour dans notre répertoire de travail
cd /learn-ansible
```

### Installation du role [springboot-service](https://github.com/orachide/ansible-role-springboot)

Nous allons utiliser un role springboot-service pour installer notre appli (cela nous permettra également de voir comment utiliser un role déja existant soit sur la galaxy Ansible soit au sein de notre entreprise). Voir le Readme du role pour plus de détails.

```sh
# Installation du role springboot-service depuis la galaxy Ansible public
ansible-galaxy install orachide.springboot-service
```

Par défaut la commande **ansible-galaxy install** va placer le role télécharger dans **./galaxy_roles/**.

```sh
# Vérifier les roles téléchargés
ls -alrt galaxy_roles/
# On retrouve 2 roles (dont geerlingguy.java qui est une dépendance du role springboot-service que nous avons installé)
```

### Création du playbook de déploiement de l'appli simple-springboot

```sh
cat > /learn-ansible/deploy-simple-springboot-app.yml <<EOF

---
- name: Deploy Simple Spring boot App
  hosts: spring-boot-app # On indique le groupe qui a été défini dans notre inventaire
  vars:
    sb_java_package: java-1.8.0-openjdk
    sb_user_groups_definitions:
      - name: sbgroup
    sb_users_definition:
      - name: Simple Spring boot App User
        username: sbuser
        groups: [sbgroup]
  roles:
    - role: orachide.springboot-service # On indique le role que nous avons installé depuis la Galaxy ainsi que les variables dont ce role aura besoin
      sb_app_name: simple-springboot-app
      sb_app_group_id: fr.runadium
      sb_app_artifact_id: simple-springboot-app
      sb_app_version: 0.0.1-SNAPSHOT
      sb_app_extension: jar
      sb_app_user: sbuser
      sb_app_user_group: sbgroup
      sb_app_artifact_file: "/simple-springboot-app/target/simple-springboot-app-0.0.1-SNAPSHOT.jar"
      sb_app_healthcheck_urls:
        - "https://localhost:8443/actuator/health"
        - "http://localhost:8080/actuator/health"
      sb_app_healthcheck_ports:
        - 8080
        - 8443

EOF
```

### Exécution du playbook d'installation de l'appli Spring Boot sur les VM du groupe spring-boot-app

```sh
# Pas besoin de préciser l'environnement parce que nous avons configuré l'environnement dev par défaut
ansible-playbook deploy-simple-springboot-app.yml
```

Pas besoin de se connecter sur chaque VM séparemment pour vérifier que les applis sont bien installées et démarées. Vous pouvez exécuter la commande suivante pour le faire. C'est un des intérets de Ansible.

```sh
# Pour vérifier que l'appli a bien été déployé sur les VM du groupe spring-boot-app.
ansible -m command -a "systemctl status simple-springboot-app" spring-boot-app
```

Vous devriez voir que pour chaque VM le statut du service simple-springboot-app est **active**

## Step 5: Création du role d'installation de HAProxy 

Maintenant que nos applis Spring Boot sont installées et démarrées, nous allons écrire le role nous permettant d'installer **HAPROXY** comme loadbalancer devant les applications Spring Boot.

Afin de pratiquer le TDD, nous allons commencé par penser aux tests de notre futur role.

### Test avec Molecule

#### Installation de molecule

```sh
# Molecule utilisera Docker pour les tests
yum install -y docker
systemctl enable docker.service
systemctl start docker.service
# Vérifier que Docker est bien installé et démarré
docker info

# Installation de prérequis
yum install -y gcc python-devel openssl-devel libffi-devel

# Installation de Molecule
pip install molecule
```

#### Creation du role HAPROXY

```sh
cd roles
# La commande suivante va créer la structure de notre role haproxy
molecule init role -r haproxy -d docker
```

La structure du répertoire du role haproxy qui a été crée par molecule est la suivante:

    haproxy/
    ├── defaults            # Contient les valeurs par défaut de notre role
    │   └── main.yml
    ├── handlers            # Contient la définition des Handlers qui seront utilisés
    │   └── main.yml
    ├── meta                # Meta données utiles si on veut déployer le role sur la galaxy
    │   └── main.yml
    ├── molecule            # Contient les tests molecule de notre role
    │   └── default
    │       ├── Dockerfile.j2
    │       ├── INSTALL.rst
    │       ├── molecule.yml
    │       ├── playbook.yml
    │       └── tests
    │           ├── test_default.py
    │           └── test_default.pyc
    ├── README.md
    ├── tasks               # Contient l'ensemble des taches (task) à exécuter
    │   └── main.yml
    └── vars                # Contient la définition des varibles qui ne changeront pratiquement jamais(constantes)
        └── main.yml

    8 directories, 12 files

#### Ecriture du test minimal avec TestInfra

### Playbook d'installation de l'HAPROXY