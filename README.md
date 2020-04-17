# Uptane OTA Server
This porject is a OTA firmware server based [django](https://www.djangoproject.com/]).Django is a python web server framework, which support database ORM model opperate.

The OTA protcol is based [uptane](https://uptane.github.io/).Uptane is an open and secure software update system design which protects software delivered over-the-air to the computerized units of automobiles. Using https://github.com/uptane/uptane as the core feature.

[Github](https://github.com/frankie-zeng/uptane-django)

## Test And Verify
I have deploy the code to myself server. ota.whyengineer.com, both https and http is support. 

## URL API

### Time server
Description: get security time

Request: GET

**get_signed_time**

`curl https://ota.whyengineer.com/get_signed_time?nonces=1,2`

It should return:

```
{"signed": {"time": "2020-04-17T08:40:40Z", "nonces": [1, 2]}, "signatures": [{"keyid": "98f447fc6256e636d3127e0df160549c49376bdf519aacf0b89aacf4137ae1e2", "method": "RSASSA-PSS", "sig": "6d8df016acd3c236ab9844439a80e703893dbd9dafa2eaf559f1487277ab9b9de13e72027ce59db00436263cb69d7b00e6b4a133913f3753235e970bf5045c9875dc6d77c073e2af556ed9a8f4dd2960fa98424a56b8805cac917572b5ae90c0d5cf3dbfff1da9dbab981bb0701a9ddf77233bfea593e08dd64bbb7ede2d83671f61ba502050093c7e473e6ce336516d12bb3bf8c070901207f80dabed7eaa9bd5cc2109f63766479426952659ddf52c4db466f452b97dd5a657bc2bea642122b2b924da9dc5989f2f71502539e28afc3467b67b04c255963f14027b7bd13d8eda4e924069957b7b1698be669c71ae050b2d4cc1ee0ef61c72c83941d2549b93"}]}
```

### Image Repo
Image Repo management the firmware of ECU.

#### Get the metadata information
`
curl http://ota.whyengineer.com/repo/metadata/root.json
`

It should return the root role metadata.

All metadata url list:

* http://ota.whyengineer.com/repo/metadata/root.json
* http://ota.whyengineer.com/repo/metadata/timestamp.json
* http://ota.whyengineer.com/repo/metadata/snapshot.json
* http://ota.whyengineer.com/repo/metadata/targets.json

or gz compressed file:
* http://ota.whyengineer.com/repo/metadata/root.json.gz
* http://ota.whyengineer.com/repo/metadata/timestamp.json.gz
* http://ota.whyengineer.com/repo/metadata/snapshot.json.gz
* http://ota.whyengineer.com/repo/metadata/targets.json.gz

#### Get the target firmware 
`
curl -u admin:admin123456 http://ota.whyengineer.com/repo/targets/hello_world.txt
`

User access targets file need username:password. 

`
http://ota.whyengineer.com/repo/targets/<filename>
`

hello_world.txt is the default firmware in the image repo.

```
the default usernamee:admin
the default password:admin123456
```

### Director Repo
Director Repo distribute the Image Repo firmware to a special VIN and special ECU

#### Register vechile manifest
Description: get security time

Request: POST

**director/register_vehicle_manifest**

* manifest
* vin
* ecu_serial

Make sure vin and ecu_serial have registed in server
```
example_manifest=
{
        "signatures": [{
            "keyid": "9a406d99e362e7c93e7acfe1e4d6585221315be817f350c026bbee84ada260da",
            "method": "ed25519",
            "sig": "335272f77357dc0e9f1b74d72eb500e4ff0f443f824b83405e2b21264778d1610e0a5f2663b90eda8ab05a28b5b64fc15514020985d8a93576fe33b287e1380f"}],
        "signed": {
            "primary_ecu_serial": "INFOdemocar",
            "vin": "democar",
            "ecu_version_manifests": {
            "TCUdemocar": [{
            "signatures": [{
                "keyid": "49309f114b857e4b29bfbff1c1c75df59f154fbc45539b2eb30c8a867843b2cb",
                "method": "ed25519",
                "sig": "fd04c1edb0ddf1089f0d3fc1cd460af584e548b230d9c290deabfaf29ce5636b6b897eaa97feb64147ac2214c176bbb1d0fa8bb9c623011a0e48d258eb3f9108"}],
            "signed": {
                "attacks_detected": "",
                "ecu_serial": "TCUdemocar",
                "previous_timeserver_time": "2017-05-18T16:37:46Z",
                "timeserver_time": "2017-05-18T16:37:48Z",
                "installed_image": {
                "filepath": "/secondary_firmware.txt",
                "fileinfo": {
                "length": 37,
                "hashes": {
                "sha256": "6b9f987226610bfed08b824c93bf8b2f59521fce9a2adef80c495f363c1c9c44",
                "sha512": "706c283972c5ae69864b199e1cdd9b4b8babc14f5a454d0fd4d3b35396a04ca0b40af731671b74020a738b5108a78deb032332c36d6ae9f31fae2f8a70f7e1ce"}}}}}]}}}
```


`
curl -data "manifest=$example_manifest,vin=democar,ecu_serial=INFOdemocar" http://ota.whyengineer.com/director/register_vehicle_manifest
`

If register ok, it should return:

`
{
    "err": 0,
    "msg": "register manifest successfully"
}
`

**every regiter online is 5min.**



#### Get the VIN metadata information(call register_vehicle_manifest firstly)
`
curl http://ota.whyengineer.com/director/democar/metadata/root.json
`

`
http://ota.whyengineer.com/director/<vin>/metadata/root.json
`

#### Get the target firmware 
`
curl -u admin:admin123456 http://ota.whyengineer.com/director/democar/targets/hello_world.txt
`

User access targets file need username:password. 

`
http://ota.whyengineer.com/director/<vin>/targets/<filename>
`

hello_world.txt is the default firmware in the image repo.

```
the default usernamee:admin
the default password:admin123456
```

## Admin Page
This feature based on django admin page.

http://ota.whyengineer.com/admin/


username:admin

password:admin123456