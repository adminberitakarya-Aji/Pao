# PAO Infrastructure - Terraform Root Module
# This is the main entry point for all infrastructure

terraform {
  required_version = ">= 1.8.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.0"
    }
    datadog = {
      source  = "datadog/datadog"
      version = "~> 3.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    bucket         = "pao-terraform-state"
    key            = "global/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "pao-terraform-locks"
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  
  default_tags {
    tags = {
      Project     = "pao"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "platform"
    }
  }
}

provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
  
  default_tags {
    tags = {
      Project     = "pao"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "platform"
    }
  }
}

provider "aws" {
  alias  = "ap_southeast_1"
  region = "ap-southeast-1"
  
  default_tags {
    tags = {
      Project     = "pao"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "platform"
    }
  }
}

provider "google" {
  alias   = "us_central1"
  project = var.gcp_project_id
  region  = "us-central1"
}

provider "google" {
  alias   = "europe_west1"
  project = var.gcp_project_id
  region  = "europe-west1"
}

provider "azurerm" {
  alias           = "eastus"
  features {}
  subscription_id = var.azure_subscription_id
}

# Global resources (Route53, CloudFront, WAF, etc.)
module "global" {
  source = "./modules/global"
  
  environment        = var.environment
  domain_name        = var.domain_name
  hosted_zone_id     = var.hosted_zone_id
  acm_certificate_arn = var.acm_certificate_arn
  
  providers = {
    aws = aws.us_east_1
  }
}

# Multi-region Kubernetes clusters
module "eks_us_east_1" {
  source = "./modules/eks"
  
  cluster_name    = "pao-${var.environment}-us-east-1"
  region          = "us-east-1"
  environment     = var.environment
  vpc_id          = module.vpc_us_east_1.vpc_id
  private_subnet_ids = module.vpc_us_east_1.private_subnet_ids
  public_subnet_ids  = module.vpc_us_east_1.public_subnet_ids
  
  node_groups = local.node_groups_us_east_1
  
  providers = {
    aws = aws.us_east_1
  }
}

module "eks_eu_west_1" {
  source = "./modules/eks"
  
  cluster_name    = "pao-${var.environment}-eu-west-1"
  region          = "eu-west-1"
  environment     = var.environment
  vpc_id          = module.vpc_eu_west_1.vpc_id
  private_subnet_ids = module.vpc_eu_west_1.private_subnet_ids
  public_subnet_ids  = module.vpc_eu_west_1.public_subnet_ids
  
  node_groups = local.node_groups_eu_west_1
  
  providers = {
    aws = aws.eu_west_1
  }
}

module "eks_ap_southeast_1" {
  source = "./modules/eks"
  
  cluster_name    = "pao-${var.environment}-ap-southeast-1"
  region          = "ap-southeast-1"
  environment     = var.environment
  vpc_id          = module.vpc_ap_southeast_1.vpc_id
  private_subnet_ids = module.vpc_ap_southeast_1.private_subnet_ids
  public_subnet_ids  = module.vpc_ap_southeast_1.public_subnet_ids
  
  node_groups = local.node_groups_ap_southeast_1
  
  providers = {
    aws = aws.ap_southeast_1
  }
}

# VPCs per region
module "vpc_us_east_1" {
  source = "./modules/vpc"
  
  name        = "pao-${var.environment}-us-east-1"
  cidr_block  = "10.0.0.0/16"
  region      = "us-east-1"
  environment = var.environment
  
  providers = {
    aws = aws.us_east_1
  }
}

module "vpc_eu_west_1" {
  source = "./modules/vpc"
  
  name        = "pao-${var.environment}-eu-west-1"
  cidr_block  = "10.1.0.0/16"
  region      = "eu-west-1"
  environment = var.environment
  
  providers = {
    aws = aws.eu_west_1
  }
}

module "vpc_ap_southeast_1" {
  source = "./modules/vpc"
  
  name        = "pao-${var.environment}-ap-southeast-1"
  cidr_block  = "10.2.0.0/16"
  region      = "ap-southeast-1"
  environment = var.environment
  
  providers = {
    aws = aws.ap_southeast_1
  }
}

# Databases (RDS, ElastiCache, DocumentDB)
module "databases_us_east_1" {
  source = "./modules/databases"
  
  environment     = var.environment
  vpc_id          = module.vpc_us_east_1.vpc_id
  private_subnet_ids = module.vpc_us_east_1.private_subnet_ids
  region          = "us-east-1"
  
  providers = {
    aws = aws.us_east_1
  }
}

module "databases_eu_west_1" {
  source = "./modules/databases"
  
  environment     = var.environment
  vpc_id          = module.vpc_eu_west_1.vpc_id
  private_subnet_ids = module.vpc_eu_west_1.private_subnet_ids
  region          = "eu-west-1"
  
  providers = {
    aws = aws.eu_west_1
  }
}

module "databases_ap_southeast_1" {
  source = "./modules/databases"
  
  environment     = var.environment
  vpc_id          = module.vpc_ap_southeast_1.vpc_id
  private_subnet_ids = module.vpc_ap_southeast_1.private_subnet_ids
  region          = "ap-southeast-1"
  
  providers = {
    aws = aws.ap_southeast_1
  }
}

# Secrets management
module "secrets" {
  source = "./modules/secrets"
  
  environment = var.environment
  
  providers = {
    aws = aws.us_east_1
  }
}

# Observability
module "observability" {
  source = "./modules/observability"
  
  environment = var.environment
  datadog_api_key = var.datadog_api_key
  
  providers = {
    aws = aws.us_east_1
  }
}

# CI/CD (GitHub Actions OIDC, ArgoCD)
module "cicd" {
  source = "./modules/cicd"
  
  environment       = var.environment
  github_org        = var.github_org
  github_repo       = var.github_repo
  
  providers = {
    aws = aws.us_east_1
  }
}

# Outputs
output "cluster_endpoints" {
  value = {
    us_east_1       = module.eks_us_east_1.cluster_endpoint
    eu_west_1       = module.eks_eu_west_1.cluster_endpoint
    ap_southeast_1  = module.eks_ap_southeast_1.cluster_endpoint
  }
}

output "database_endpoints" {
  value = {
    us_east_1       = module.databases_us_east_1.endpoints
    eu_west_1       = module.databases_eu_west_1.endpoints
    ap_southeast_1  = module.databases_ap_southeast_1.endpoints
  }
  sensitive = true
}